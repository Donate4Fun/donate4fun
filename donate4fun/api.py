import logging
from uuid import UUID
from functools import partial
from urllib.parse import urlencode
from datetime import datetime

import bugsnag
import ecdsa
from fastapi import FastAPI, WebSocket, Request, Depends, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse
from lnurl.core import _url_encode as lnurl_encode
from lnpayencode import lndecode, LnAddr
from anyio.abc import TaskStatus
from rollbar.contrib.fastapi.routing import RollbarLoggingRoute
from starlette.datastructures import URL
from httpx import HTTPStatusError
from pydantic import ValidationError as PydanticValidationError

from .models import (
    Donation, Donator, Invoice, DonateResponse, DonateRequest, YoutubeChannel,
    WithdrawalToken, BaseModel, Notification, Credentials, SubscribeEmailRequest,
)
from .types import ValidationError, RequestHash, PaymentRequest
from .donatees import apply_target
from .db_models import DonationDb, WithdrawalDb
from .db import NoResultFound
from .settings import settings
from .api_utils import get_donator, load_donator, get_db_session, task_group
from .lnd import PayInvoiceError, LnurlWithdrawResponse, lnd
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
    body = exc.response.json()
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
    logger.debug(f"Donator {donator.id} wants to donate {request.amount} to {request.target or request.channel_id}")
    donation = Donation(
        amount=request.amount,
        donator=donator,
    )
    if request.receiver_id:
        # Donation to a donator - possibly just an own balance fulfillment
        receiver = await load_donator(db_session, request.receiver_id)
        if receiver.lnauth_pubkey is None:
            raise ValidationError("Money receiver should have a connected wallet")
        donation.receiver = receiver
    elif request.channel_id:
        donation.youtube_channel = await db_session.query_youtube_channel(youtube_channel_id=request.channel_id)
    elif request.twitter_account_id:
        donation.twitter_account = await db_session.query_twitter_account(id=request.twitter_account_id)
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
    use_balance = request.receiver_id != donator.id and donator.balance >= request.amount
    if not use_balance:
        invoice: Invoice = await lnd.create_invoice(memo=make_memo(donation), value=request.amount)
        donation.r_hash = invoice.r_hash  # This hash is needed to find and complete donation after payment succeeds
    await db_session.create_donation(donation)
    if use_balance:
        await db_session.donation_paid(donation_id=donation.id, amount=request.amount, paid_at=datetime.utcnow())
        donation = await db_session.query_donation(id=donation.id)
        # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
        web_request.session['balance'] = (await db_session.query_donator(donator.id)).balance
        return DonateResponse(donation=donation, payment_request=None)
    else:
        return DonateResponse(donation=donation, payment_request=invoice.payment_request)


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def donation(donation_id: UUID, db_session=Depends(get_db_session)):
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


@router.post("/donation/{donation_id}/cancel")
async def cancel_donation(donation_id: UUID, db=Depends(get_db_session)):
    """
    It only works for HODL invoices
    """
    r_hash: RequestHash = await db.cancel_donation(donation_id)
    await lnd.cancel_invoice(r_hash)


@router.get("/donations/latest", response_model=list[Donation])
async def latest_donations(db=Depends(get_db_session)):
    return await db.query_donations(
        DonationDb.paid_at.isnot(None) & DonationDb.youtube_channel_id.isnot(None),
        limit=settings.latest_donations_count,
    )


@router.get("/donations/by-donator/{donator_id}", response_model=list[Donation])
async def donator_donations(donator_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations((DonationDb.donator_id == donator_id) & DonationDb.paid_at.isnot(None))


class StatusResponse(BaseModel):
    db: str
    lnd: str


@router.get("/status")
async def status(db=Depends(get_db_session)):
    return StatusResponse(
        db=await db.query_status(),
        lnd=await lnd.query_state(),
    )


class MeResponse(BaseModel):
    donator: Donator
    youtube_channels: list[YoutubeChannel]


@router.get("/donator/me", response_model=MeResponse)
async def me(request: Request, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    linked_youtube_channels: list[YoutubeChannel] = await db.query_donator_youtube_channels(donator.id)
    # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
    request.session['balance'] = donator.balance
    request.session['lnauth_pubkey'] = donator.lnauth_pubkey
    return MeResponse(donator=donator, youtube_channels=linked_youtube_channels)


@router.get("/donator/{donator_id}", response_model=Donator)
async def donator(request: Request, donator_id: UUID, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator_id)
    if donator.id != me.id:
        donator.balance = 0  # Do not show balance to others
    return donator


@router.get('/lnurl/withdraw', response_model=LnurlWithdrawResponse)
async def lnurl_withdraw(request: Request, token: str, db=Depends(get_db_session)):
    decoded = WithdrawalToken.from_jwt(token)
    withdrawal: WithdrawalDb = await db.query_withdrawal(decoded.withdrawal_id)
    donator: Donator = await db.query_donator(withdrawal.donator.id)
    callback_url = f"{settings.lnd.lnurl_base_url}{URL(request.url_for('withdraw_callback')).path}"
    return LnurlWithdrawResponse(
        callback=callback_url,
        k1=token,
        default_description=f'Donate4.Fun withdrawal for "{donator.name}"',
        min_withdrawable=settings.min_withdraw * 1000,
        max_withdrawable=donator.balance * 1000,
    )


@router.get('/lnurl/withdraw-callback', response_class=JSONResponse)
async def withdraw_callback(request: Request, k1: str, pr: str, db=Depends(get_db_session)):
    try:
        token = WithdrawalToken.from_jwt(k1)
        withdrawal: WithdrawalDb = await db.query_withdrawal(token.withdrawal_id)
        donator: Donator = await db.query_donator(withdrawal.donator.id)
        invoice: LnAddr = lndecode(pr)
        invoice_amount_sats = invoice.amount * 10**8
        min_amount = settings.min_withdraw
        max_amount = donator.balance
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
    except Exception as exc:
        logger.exception("Exception while initiating payment")
        return dict(status="ERROR", reason=f"Error while initiating payment: {exc}")
    else:
        return dict(status="OK")


@router.get('/lnurl/payment-callback', response_class=JSONResponse)
async def payment_callback(request: Request, ):
    pass


async def send_withdrawal(
    *, withdrawal_id: UUID, payment_request: PaymentRequest, amount: int, lnd, db,
    task_status: TaskStatus,
):
    try:
        async with db.session() as db_session:
            await db_session.withdraw(withdrawal_id=withdrawal_id, amount=amount)
            task_status.started()
            await lnd.pay_invoice(payment_request)
    except PayInvoiceError as exc:
        logger.exception("Failed to send withdrawal payment")
        if settings.bugsnag.enabled:
            bugsnag.notify(exc)
        async with db.session() as db_session:
            await db_session.notify(
                f'withdrawal:{withdrawal_id}',
                Notification(id=withdrawal_id, status='ERROR', message=str(exc)),
            )
    except Exception as exc:
        logger.exception("Internal error in send_withdrawal")
        if settings.bugsnag.enabled:
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
    except Exception as exc:
        logger.exception("Error in lnuath callback")
        return dict(status="ERROR", reason=str(exc))
    else:
        return dict(status="OK")


@router.post('/disconnect-wallet')
async def disconnect_wallet(db=Depends(get_db_session), donator=Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    if donator.balance > 0:
        raise ValidationError("Could not disconnect LN wallet with positive balance")
    await db.login_donator(donator.id, key=None)


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


@router.get("/donatee/recently-donated", response_model=list[YoutubeChannel])
async def recently_donated_donatees(db=Depends(get_db_session)):
    return await db.query_recently_donated_donatees(limit=20)


@router.post("/subscribe-email", response_model=UUID | None)
async def subscribe_email(request: SubscribeEmailRequest, db=Depends(get_db_session)):
    return await db.save_email(request.email)


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
    withdrawal_id: UUID = await db.create_withdrawal(donator=me)
    token = WithdrawalToken(
        withdrawal_id=withdrawal_id,
    )
    url = f"{settings.lnd.lnurl_base_url}{URL(request.url_for('lnurl_withdraw')).path}"
    withdraw_url = URL(url).include_query_params(token=token.to_jwt())
    return WithdrawResponse(
        lnurl=lnurl_encode(str(withdraw_url)),
        amount=me.balance,
        withdrawal_id=withdrawal_id,
    )
