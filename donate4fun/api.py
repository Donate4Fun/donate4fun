import logging
import hashlib
import json
from uuid import UUID
from functools import partial
from urllib.parse import urlencode
from datetime import datetime

import bugsnag
import ecdsa
import httpx
import posthog
from fastapi import FastAPI, WebSocket, Request, Depends, Query, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from lnurl.core import _url_encode as lnurl_encode
from lnpayencode import LnAddr
from anyio.abc import TaskStatus
from rollbar.contrib.fastapi.routing import RollbarLoggingRoute
from starlette.datastructures import URL
from httpx import HTTPStatusError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from .models import (
    Donation, Donator, Invoice, DonateResponse, DonateRequest,
    WithdrawalToken, BaseModel, Notification, Credentials, SubscribeEmailRequest,
    DonatorStats, DonationPaidRequest, PayInvoiceResult, Donatee,
)
from .types import ValidationError, RequestHash, PaymentRequest
from .core import to_base64
from .donatees import apply_target
from .db_models import DonationDb, WithdrawalDb
from .db_donations import sent_donations_subquery, received_donations_subquery
from .settings import settings
from .api_utils import get_donator, load_donator, get_db_session, task_group, only_me, track_donation
from .lnd import PayInvoiceError, LnurlWithdrawResponse, lnd, lightning_payment_metadata
from .pubsub import pubsub
from .twitter import query_or_fetch_twitter_account
from . import api_twitter, api_youtube


logger = logging.getLogger(__name__)
router = app = FastAPI()
router.route_class = RollbarLoggingRoute
app.include_router(api_twitter.router)
app.include_router(api_youtube.router)
app.include_router(api_youtube.legacy_router)


@app.exception_handler(HTTPStatusError)
def http_status_error_handler(request, exc):
    logger.debug(f"{request.url}: Upstream error", exc_info=exc)
    status_code = exc.response.status_code
    if 'application/json' in exc.response.headers.get('content-type', ''):
        body = exc.response.json()
    else:
        body = exc.response.text
    return JSONResponse(status_code=500, content={"message": f"Upstream server returned {status_code}: {body}"})


@app.exception_handler(NoResultFound)
def no_result_found_handler(request, exc):
    return JSONResponse(status_code=404, content=dict(message="Item not found"))


@app.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=dict(
            status="error",
            type=type(exc).__name__,
            error=str(exc),
        ),
    )


@app.exception_handler(PydanticValidationError)
def pydantic_validation_error_handler(request, exc):
    logger.debug(f"{request.url}: Validation error", exc_info=exc)
    return JSONResponse(
        status_code=400,
        content=dict(
            status="error",
            type=type(exc).__name__,
            error=exc.errors()[0]['msg'],
        ),
    )


def make_memo(donation: Donation) -> str:
    if donation.youtube_channel:
        return f"Donate4.Fun to {donation.youtube_channel.title}"
    elif donation.twitter_account:
        return f"Donate4.Fun to {donation.twitter_account.handle}"
    elif donation.receiver:
        if donation.receiver.id == donation.donator.id:
            return f"[Donate4.fun] fulfillment for {donation.receiver.name}"
        else:
            return f"[Donate4.fun] donation to {donation.receiver.name}"
    else:
        raise ValueError(f"Could not make a memo for donation {donation}")


@router.post("/donate", response_model=DonateResponse)
async def donate(
    web_request: Request, request: DonateRequest, donator: Donator = Depends(get_donator), db_session=Depends(get_db_session),
 ) -> DonateResponse:
    logger.debug(
        "Donator %s wants to donate %d to %s",
        donator.id, request.amount, request.target or request.channel_id or request.lightning_address,
    )
    donation = Donation(
        amount=request.amount,
        donator=donator,
    )
    if request.lightning_address:
        donation.lightning_address = request.lightning_address
    if request.receiver_id:
        # Donation to a donator - possibly just an own balance fulfillment
        receiver = await load_donator(db_session, request.receiver_id)
        if not receiver.connected:
            raise ValidationError("Money receiver should have a connected wallet")
        donation.receiver = receiver
    elif request.channel_id:
        donation.youtube_channel = await db_session.query_youtube_channel(youtube_channel_id=request.channel_id)
        donation.lightning_address = donation.youtube_channel.lightning_address
    elif request.twitter_account_id:
        donation.twitter_account = await db_session.query_twitter_account(id=request.twitter_account_id)
        donation.lightning_address = donation.twitter_account.lightning_address
    elif request.target:
        await apply_target(donation, request.target, db_session)
    else:
        raise ValidationError("donation should have a target, channel_id or receiver_id")
    if request.donator_twitter_handle:
        donation.donator_twitter_account = await query_or_fetch_twitter_account(
            db=db_session, handle=request.donator_twitter_handle,
        )
    donator = await load_donator(db_session, donator.id)
    # If donator has enough money (and not fulfilling his own balance) - try to pay donation instantly
    use_balance = (
        request.receiver_id != donator.id
        and (donator.available_balance if donation.lightning_address else donator.balance) >= request.amount
    )
    if donation.lightning_address:
        pay_req: PaymentRequest = await fetch_lightning_address(donation)
        r_hash = RequestHash(pay_req.decode().paymenthash)
        if use_balance:
            # FIXME: this leads to 'duplicate key value violates unique constraint "donation_rhash_key"'
            # if we are donating to a local lightning address
            donation.r_hash = r_hash
        else:
            donation.transient_r_hash = r_hash
    elif not use_balance:
        invoice: Invoice = await lnd.create_invoice(memo=make_memo(donation), value=request.amount)
        donation.r_hash = invoice.r_hash  # This hash is needed to find and complete donation after payment succeeds
        pay_req = invoice.payment_request
    await db_session.create_donation(donation)
    if use_balance:
        if donation.lightning_address:
            pay_result: PayInvoiceResult = await lnd.pay_invoice(pay_req)
            amount = pay_result.value_sat
            paid_at = pay_result.creation_date
            fee_msat = pay_result.fee_msat
            claimed_at = pay_result.creation_date
        else:
            amount = request.amount
            paid_at = datetime.utcnow()
            fee_msat = None
            claimed_at = None
        await db_session.donation_paid(
            donation_id=donation.id, amount=amount, paid_at=paid_at, fee_msat=fee_msat, claimed_at=claimed_at,
        )
        donation = await db_session.query_donation(id=donation.id)
        # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
        web_request.session['balance'] = (await db_session.query_donator(id=donator.id)).balance
        track_donation(donation)
        return DonateResponse(donation=donation, payment_request=None)
    else:
        return DonateResponse(donation=donation, payment_request=pay_req)


class LnurlpError(Exception):
    pass


async def fetch_lightning_address(donation: Donation) -> PaymentRequest:
    name, host = donation.lightning_address.split('@', 1)
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://{host}/.well-known/lnurlp/{name}', follow_redirects=True)
        response.raise_for_status()
        metadata = response.json()
        # https://github.com/lnurl/luds/blob/luds/06.md
        if metadata.get('status', 'OK') != 'OK':
            raise LnurlpError(f"Status is not OK: {metadata}")
        if not metadata['minSendable'] <= donation.amount * 1000 <= metadata['maxSendable']:
            raise LnurlpError(f"Amount is out of bounds: {donation.amount} {metadata}")
        fields = dict(json.loads(metadata['metadata']))
        if donation.donator_twitter_account:
            name = '@' + donation.donator_twitter_account.handle
        else:
            name = donation.donator.name
        params = dict(amount=donation.amount * 1000)
        if payerdata_request := metadata.get('payerData'):
            payerdata = {}
            if 'name' in payerdata_request:
                payerdata['name'] = f'{name} via Donate4.Fun'
            params['payerdata'] = json.dumps(payerdata, separators=(',', ':'))
        if donation.youtube_video:
            target = f'https://youtube.com/watch?v={donation.youtube_video.video_id}'
        elif donation.twitter_tweet:
            target = f'https://twitter.com/{donation.twitter_account.handle}/status/{donation.twitter_tweet.tweet_id}'
        elif donation.youtube_channel:
            target = f'https://youtube.com/channel/{donation.youtube_channel.channel_id}'
        elif donation.twitter_account:
            target = f'https://twitter.com/{donation.twitter_account.handle}'
        elif donation.lightning_address:
            target = fields.get('text/identifier', donation.lightning_address)
        comment = f'Tip from {name} via Donate4.Fun for {target}'
        if 'commentAllowed' in metadata:
            params['comment'] = comment[:metadata['commentAllowed']]
        response = await client.get(metadata['callback'], params=params)
        try:
            response.raise_for_status()
        except Exception as exc:
            raise LnurlpError(response.content) from exc
        data = response.json()
        if data.get('status', 'OK') != 'OK':
            raise LnurlpError(f"Status is not OK: {data}")
        pay_req = PaymentRequest(data['pr'])
        invoice: LnAddr = pay_req.decode()
        expected_hash = dict(invoice.tags)['h']
        # https://github.com/lnurl/luds/blob/luds/18.md#3-committing-payer-to-the-invoice
        full_metadata: str = metadata['metadata'] + params.get('payerdata', '')
        if sha256hash(full_metadata) != expected_hash:
            raise LnurlpError(f"Metadata hash does not match invoice hash: sha256({full_metadata}) != {expected_hash}")
        invoice_amount = invoice.amount * 10 ** 8
        if invoice_amount != donation.amount:
            raise LnurlpError(f"Amount in invoice does not match requested amount: {invoice_amount} != {donation.amount}")
        return pay_req


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def get_donation(donation_id: UUID, db_session=Depends(get_db_session)):
    donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.lookup_invoice(donation.r_hash)
        if invoice is None or invoice.state == 'CANCELED':
            logger.debug(f"Invoice {invoice} cancelled, recreating")
            invoice = await lnd.create_invoice(memo=make_memo(donation), value=donation.amount)
            await db_session.update_donation(donation_id=donation_id, r_hash=invoice.r_hash)
        payment_request = invoice.payment_request
    else:
        payment_request = None
    return DonateResponse(donation=donation, payment_request=payment_request)


@router.post("/donation/{donation_id}/paid", response_model=Donation)
async def donation_paid(donation_id: UUID, request: DonationPaidRequest, db=Depends(get_db_session)):
    donation: Donation = await db.query_donation(id=donation_id)
    if donation.lightning_address is None:
        # Do nothing for all other cases
        return
    digest = RequestHash(hashlib.sha256(bytes.fromhex(request.preimage)).digest())
    if digest != donation.transient_r_hash:
        raise ValidationError(f"Preimage hash does not match {digest}")
    if request.route.total_amt != donation.amount:
        raise ValidationError(f"Donation amount do not match {request.route.total_amt}")
    now = datetime.utcnow()
    await db.donation_paid(donation.id, donation.amount, paid_at=now, fee_msat=request.route.total_fees * 1000, claimed_at=now)
    donation = await db.query_donation(id=donation.id)
    track_donation(donation)
    return donation


@router.post("/donation/{donation_id}/cancel")
async def cancel_donation(donation_id: UUID, db=Depends(get_db_session), me=Depends(get_donator)):
    """
    It only works for HODL invoices
    """
    donation: Donation = await db.cancel_donation(donation_id)
    if donation.donator.id != me.id:
        # Exception will rollback the transaction
        raise HTTPException(status_code=403, detail="You are not the donator")
    if donation.r_hash is not None:
        await lnd.cancel_invoice(donation.r_hash)


@router.get("/donations/latest", response_model=list[Donation])
async def latest_donations(db=Depends(get_db_session)):
    return await db.query_donations(
        DonationDb.paid_at.isnot(None) & DonationDb.youtube_channel_id.isnot(None),
        limit=settings.latest_donations_count,
    )


@router.get("/donations/by-donator/{donator_id}", response_model=list[Donation])
async def donator_donations(donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me), offset: int = 0):
    return await db.query_donations(
        DonationDb.paid_at.isnot(None) & (
            (DonationDb.donator_id == donator_id)
            | (DonationDb.receiver_id == donator_id)
        ),
        offset=offset,
    )


@router.get("/donations/by-donator/{donator_id}/sent", response_model=list[Donation])
async def donator_donations_sent(donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me), offset: int = 0):
    return await db.query_donations(DonationDb.id.in_(select(sent_donations_subquery(donator_id).c.id)), offset=offset)


@router.get("/donations/by-donator/{donator_id}/received", response_model=list[Donation])
async def donator_donations_received(donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me), offset: int = 0):
    return await db.query_donations(DonationDb.id.in_(select(received_donations_subquery(donator_id).c.id)), offset=offset)


class StatusResponse(BaseModel):
    db: str
    lnd: str


@router.head("/status")
@router.get("/status")
async def status(db=Depends(get_db_session)):
    return StatusResponse(
        db=await db.query_status(),
        lnd=await lnd.query_state(),
    )


@router.get("/me", response_model=Donator)
async def new_me(request: Request, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    me = await load_donator(db, me.id)
    # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
    request.session['balance'] = me.balance
    request.session['lnauth_pubkey'] = me.lnauth_pubkey
    request.session['connected'] = me.connected
    return me


class MeResponse(BaseModel):
    donator: Donator
    youtube_channels: list


@router.get("/donator/me", response_model=MeResponse, deprecated=True)
async def me(request: Request, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    """
    Deprecated, remove when all browser extension instances update
    """
    me = await load_donator(db, me.id)
    # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
    request.session['balance'] = me.balance
    request.session['lnauth_pubkey'] = me.lnauth_pubkey
    return MeResponse(donator=me, youtube_channels=[])


class DonatorResponse(BaseModel):
    id: UUID
    name: str
    avatar_url: str
    lightning_address: str | None


@router.get("/donator/{donator_id}", response_model=DonatorResponse)
async def donator(request: Request, donator_id: UUID, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator_id)
    return DonatorResponse(**donator.dict())


@router.get("/donator/{donator_id}/stats", response_model=DonatorStats)
async def donator_stats(request: Request, donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me)):
    return await db.query_donator_stats(donator_id)


@router.get('/lnurl/withdraw', response_model=LnurlWithdrawResponse)
async def lnurl_withdraw(request: Request, token: str, db=Depends(get_db_session)):
    decoded = WithdrawalToken.from_jwt(token)
    withdrawal: WithdrawalDb = await db.query_withdrawal(decoded.withdrawal_id)
    donator: Donator = await db.query_donator(id=withdrawal.donator.id)
    callback_url = f"{settings.lnd.lnurl_base_url}{URL(request.url_for('withdraw_callback')).path}"
    return LnurlWithdrawResponse(
        callback=callback_url,
        k1=token,
        default_description=f'Donate4.Fun withdrawal for "{donator.name}"',
        min_withdrawable=settings.min_withdraw * 1000,
        max_withdrawable=donator.available_balance * 1000,
    )


@router.get('/lnurl/withdraw-callback', response_class=JSONResponse)
async def withdraw_callback(request: Request, k1: str, pr: PaymentRequest, db=Depends(get_db_session)):
    try:
        token = WithdrawalToken.from_jwt(k1)
        withdrawal: WithdrawalDb = await db.query_withdrawal(token.withdrawal_id)
        donator: Donator = await db.query_donator(id=withdrawal.donator.id)
        invoice: LnAddr = pr.decode()
        invoice_amount_sats = invoice.amount * 10**8
        min_amount = settings.min_withdraw
        max_amount = donator.available_balance
        if invoice_amount_sats < min_amount or invoice_amount_sats > max_amount:
            raise ValidationError(
                f"Invoice amount {invoice_amount_sats} is not in allowed bounds [{min_amount}, {max_amount}]"
            )
        # According to https://github.com/fiatjaf/lnurl-rfc/blob/luds/03.md payment should not block response
        await task_group.start(partial(
            send_withdrawal,
            withdrawal_id=withdrawal.id,
            amount=invoice_amount_sats,
            payment_request=pr,
            lnd=lnd,
            db=db.db,
        ))
        posthog.capture(donator.id, 'withdraw', dict(amount=invoice_amount_sats, withdrawal_id=withdrawal.id))
    except Exception as exc:
        logger.exception("Exception while initiating payment")
        return dict(status="ERROR", reason=f"Error while initiating payment: {exc}")
    else:
        return dict(status="OK")


class WithdrawWithInvoiceRequest(BaseModel):
    invoice: PaymentRequest


@router.post('/me/withdraw')
async def withdraw_with_invoice(request: WithdrawWithInvoiceRequest, me=Depends(only_me)):
    pass


class PaymentCallbackResponse(BaseModel):
    status: str
    pr: PaymentRequest


@router.get('/lnurl/{receiver_id}/payment-callback', response_model=PaymentCallbackResponse)
async def payment_callback(
    request: Request, receiver_id: UUID, amount: int = Query(...), comment: str = Query(...), db_session=Depends(get_db_session),
):
    """
    This callback is needed for lightning address support. Currently it's used for internal testing only.
    """
    receiver: Donator = await db_session.query_donator(id=receiver_id)
    amount = amount // 1000  # FIXME: handle msats correctly
    invoice: Invoice = await lnd.create_invoice(
        memo=comment, value=amount, description_hash=to_base64(sha256hash(lightning_payment_metadata(receiver))),
    )
    donation = Donation(
        amount=amount,
        donator=None,
        r_hash=invoice.r_hash,  # This hash is needed to find and complete donation after payment succeeds
        receiver=Donator(id=receiver_id),
        # FIXME: save comment
    )
    await db_session.create_donation(donation)
    return PaymentCallbackResponse(
        status='OK',
        pr=invoice.payment_request,
    )


def sha256hash(data: str) -> bytes:
    return hashlib.sha256(data.encode()).digest()


async def send_withdrawal(
    *, withdrawal_id: UUID, payment_request: PaymentRequest, amount: int, lnd, db,
    task_status: TaskStatus,
):
    try:
        async with db.session() as db_session:
            await db_session.start_withdraw(withdrawal_id=withdrawal_id, amount=amount, fee_msat=settings.fee_limit * 1000)
            task_status.started()
            result: PayInvoiceResult = await lnd.pay_invoice(payment_request)
            await db_session.finish_withdraw(withdrawal_id=withdrawal_id, fee_msat=result.fee_msat)
    except PayInvoiceError as exc:
        logger.exception("Failed to send withdrawal payment")
        if settings.bugsnag:
            bugsnag.notify(exc)
        async with db.session() as db_session:
            await db_session.notify(
                f'withdrawal:{withdrawal_id}',
                Notification(id=withdrawal_id, status='ERROR', message=str(exc)),
            )
    except Exception as exc:
        logger.exception("Internal error in send_withdrawal")
        if settings.bugsnag:
            bugsnag.notify(exc)
        raise


class LoginLnurlResponse(BaseModel):
    lnurl: str


@router.get('/lnauth/{nonce}', response_model=LoginLnurlResponse)
async def login_lnauth(request: Request, nonce: UUID, donator=Depends(get_donator)):
    url_start = f"{settings.lnd.lnurl_base_url}{URL(request.url_for('lnauth_callback')).path}"
    query_string = urlencode(dict(
        tag='login',
        k1=donator.id.bytes.hex() + nonce.bytes.hex(),  # k1 size should be 32 bytes
        action='link',
    ))
    return LoginLnurlResponse(lnurl=lnurl_encode(f'{url_start}?{query_string}'))


@router.get('/lnauth-callback', response_class=JSONResponse)
async def lnauth_callback(
    request: Request, k1: str = Query(...), sig: str = Query(...), key: str = Query(...), db_session=Depends(get_db_session),
):
    try:
        k1_bytes = bytes.fromhex(k1)
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(key), curve=ecdsa.SECP256k1)
        vk.verify_digest(bytes.fromhex(sig), k1_bytes, sigdecode=ecdsa.util.sigdecode_der)
        donator_id = UUID(bytes=k1_bytes[:16])
        nonce = UUID(bytes=k1_bytes[16:])
        credentials: Credentials = await db_session.login_donator(donator_id, key=key)
        await db_session.notify(f'lnauth:{nonce}', Notification(
            id=nonce,
            status='ok',
            message=credentials.to_jwt(),
        ))
        posthog.capture(credentials.donator, 'connect-wallet')
    except Exception as exc:
        logger.exception("Error in lnuath callback")
        return dict(status="ERROR", reason=str(exc))
    else:
        return dict(status="OK")


@router.post('/disconnect-wallet')
async def disconnect_wallet(db=Depends(get_db_session), donator=Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    donator.lnauth_pubkey = None
    await db.save_donator(donator)
    donator = await db.query_donator(donator.id)
    if donator.balance > 0 and not donator.connected:
        raise ValidationError("Could not disconnect LN wallet with positive balance")
    posthog.capture(donator.id, 'disconnect-wallet')


@router.websocket('/subscribe/{topic}')
async def subscribe(websocket: WebSocket, topic: str):
    logger.trace("Websocket connection request: %s", topic)

    async def send_to_websocket(msg: str):
        await websocket.send_text(msg)

    await websocket.accept()
    logger.trace("Websocket connection accepted: %s", topic)
    async with pubsub.subscribe(topic, send_to_websocket):
        while True:
            try:
                msg = await websocket.receive_json()
            except WebSocketDisconnect:
                logger.debug(f"Websocket {topic} disconnected")
                break
            else:
                logger.debug(f"Received '{msg}' from websocket for topic {topic}")


class UpdateSessionRequest(BaseModel):
    creds_jwt: str


@router.post('/update-session')
async def update_session(request: Request, req: UpdateSessionRequest):
    creds = Credentials.from_jwt(req.creds_jwt)
    request.session.update(**creds.to_json_dict())
    posthog.capture(creds.donator, 'update-session')


@router.get("/donatee/recently-donated", response_model=list[Donatee])
async def recently_donated_donatees(db=Depends(get_db_session)):
    return await db.query_recently_donated_donatees(limit=20)


@router.post("/subscribe-email", response_model=UUID | None)
async def subscribe_email(request: SubscribeEmailRequest, db=Depends(get_db_session), me=Depends(get_donator)):
    subscription_id: UUID = await db.save_email(request.email)
    posthog.capture(me.id, 'subscribe-email')
    return subscription_id


class WithdrawResponse(BaseModel):
    lnurl: str
    amount: int
    withdrawal_id: UUID


@router.get('/me/withdraw', response_model=WithdrawResponse)
async def withdraw(request: Request, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    # Refresh balance
    me = await load_donator(db, me.id)
    if me.balance < settings.min_withdraw:
        raise ValidationError(f"Minimum amount to withdraw is {settings.min_withdraw}, but available only {me.balance}.")
    withdrawal: WithdrawalDb = await db.create_withdrawal(donator=me)
    token = WithdrawalToken(
        withdrawal_id=withdrawal.id,
    )
    url = f"{settings.lnd.lnurl_base_url}{URL(request.url_for('lnurl_withdraw')).path}"
    withdraw_url = URL(url).include_query_params(token=token.to_jwt())
    return WithdrawResponse(
        lnurl=lnurl_encode(str(withdraw_url)),
        amount=withdrawal.amount,
        withdrawal_id=withdrawal.id,
    )
