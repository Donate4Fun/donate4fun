import logging
import math
from uuid import UUID, uuid4
from typing import Literal
from functools import partial
from urllib.parse import urlencode
from datetime import datetime

import bugsnag
import ecdsa
from fastapi import APIRouter, WebSocket, Request, Depends, HTTPException, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.datastructures import URL
from pydantic import AnyHttpUrl, Field, AnyUrl
from lnurl.models import LnurlResponseModel
from lnurl.types import MilliSatoshi
from lnurl.core import _url_encode as lnurl_encode
from lnpayencode import lndecode, LnAddr
from aiogoogle import Aiogoogle
from anyio.abc import TaskStatus
from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

from .core import get_db_session, get_lnd, get_pubsub
from .models import (
    Donation, Donator, Invoice, DonateResponse, DonateRequest, YoutubeChannelRequest, YoutubeChannel, YoutubeVideo,
    WithdrawalToken, BaseModel, Notification, Credentials, SubscribeEmailRequest,
)
from .types import ValidationError, RequestHash, PaymentRequest
from .youtube import (
    validate_target, apply_target, find_comment, YoutubeDonatee, query_or_fetch_youtube_video,
    query_or_fetch_youtube_channel, ChannelInfo, fetch_user_channel,
)
from .db import NoResultFound, DonationDb, DbSession, WithdrawalDb
from .settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()
router.route_class = RollbarLoggingRoute


def get_donator(request: Request):
    creds = Credentials(**request.session)
    if creds.donator is not None:
        donator = Donator(id=creds.donator)
    else:
        donator = Donator(id=uuid4())
        creds.donator = donator.id
    request.session.update(**creds.to_json_dict())
    return donator


def make_memo(donation: Donation) -> str:
    if donation.youtube_channel:
        return f"Donate4.fun to {donation.youtube_channel.title}"
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
    lnd=Depends(get_lnd),
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
    elif request.target:
        await apply_target(donation, request.target, db_session)
    else:
        raise ValidationError("donation should have a target, channel_id or receier_id")
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


@router.post("/donatee", response_model=YoutubeChannel)
async def donatee_by_url(request: YoutubeChannelRequest, db=Depends(get_db_session)):
    donatee: YoutubeDonatee = await validate_target(request.target)
    if donatee.video_id:
        youtube_video = await query_or_fetch_youtube_video(video_id=donatee.video_id, db=db)
        youtube_channel = youtube_video.channel
    elif donatee.channel_id:
        youtube_channel = await query_or_fetch_youtube_channel(channel_id=donatee.channel_id, db=db)
    return youtube_channel


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def donation(donation_id: UUID, db_session=Depends(get_db_session), lnd=Depends(get_lnd)):
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
async def cancel_donation(donation_id: UUID, db=Depends(get_db_session), lnd=Depends(get_lnd)):
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


@router.get("/donations/by-donatee/{donatee_id}", response_model=list[Donation])
async def donatee_donations(donatee_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations((DonationDb.youtube_channel_id == donatee_id) & DonationDb.paid_at.isnot(None))


class StatusResponse(BaseModel):
    db: str
    lnd: str


@router.get("/status")
async def status(db=Depends(get_db_session), lnd=Depends(get_lnd)):
    return StatusResponse(
        db=await db.query_status(),
        lnd=await lnd.query_state(),
    )


class MeResponse(BaseModel):
    donator: Donator
    youtube_channels: list[YoutubeChannel]


async def load_donator(db: DbSession, donator_id: UUID) -> Donator:
    try:
        return await db.query_donator(donator_id)
    except NoResultFound:
        return Donator(id=donator_id)


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


@router.get("/youtube-channel/{channel_id}", response_model=YoutubeChannel)
async def youtube_channel(channel_id: UUID, db=Depends(get_db_session)):
    return await db.query_youtube_channel(channel_id)


class WithdrawResponse(BaseModel):
    lnurl: str
    amount: int
    withdrawal_id: UUID


@router.get('/youtube-channel/{channel_id}/withdraw', response_model=WithdrawResponse)
async def withdraw(request: Request, channel_id: UUID, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    linked_youtube_channels: list[YoutubeChannel] = await db.query_donator_youtube_channels(donator.id)
    linked_youtube_channel_ids = [channel.id for channel in linked_youtube_channels]

    if channel_id not in linked_youtube_channel_ids:
        raise HTTPException(status_code=403, detail="You should prove that you own YouTube channel")
    youtube_channel = await db.query_youtube_channel(youtube_channel_id=channel_id)
    if youtube_channel.balance < settings.min_withdraw:
        raise ValidationError(
            f"You can't withdraw less than {settings.min_withdraw}, but available only {youtube_channel.balance}"
        )
    withdrawal_id: UUID = await db.create_withdrawal(youtube_channel_id=youtube_channel.id, donator_id=donator.id)
    token = WithdrawalToken(
        withdrawal_id=withdrawal_id,
    )
    url = request.app.url_path_for('lnurl_withdraw').make_absolute_url(settings.lnd.lnurl_base_url)
    withdraw_url = URL(url).include_query_params(token=token.to_jwt())
    return WithdrawResponse(
        lnurl=lnurl_encode(str(withdraw_url)),
        amount=youtube_channel.balance,
        withdrawal_id=withdrawal_id,
    )


class LnurlWithdrawResponse(LnurlResponseModel):
    """
    Override default lnurl model to allow http:// callback urls
    """
    tag: Literal["withdrawRequest"] = "withdrawRequest"
    callback: AnyUrl
    k1: str
    min_withdrawable: MilliSatoshi = Field(..., alias="minWithdrawable")
    max_withdrawable: MilliSatoshi = Field(..., alias="maxWithdrawable")
    default_description: str = Field("", alias="defaultDescription")

    @property
    def min_sats(self) -> int:
        return int(math.ceil(self.min_withdrawable / 1000))

    @property
    def max_sats(self) -> int:
        return int(math.floor(self.max_withdrawable / 1000))


@router.get('/lnurl/withdraw', response_model=LnurlWithdrawResponse)
async def lnurl_withdraw(request: Request, token: str, db=Depends(get_db_session)):
    decoded = WithdrawalToken.from_jwt(token)
    withdrawal: WithdrawalDb = await db.query_withdrawal(decoded.withdrawal_id)
    return LnurlWithdrawResponse(
        callback=request.app.url_path_for('withdraw_callback').make_absolute_url(settings.lnd.lnurl_base_url),
        k1=token,
        default_description=f'Donate4.Fun withdrawal for "{withdrawal.youtube_channel.title}"',
        min_withdrawable=settings.min_withdraw * 1000,
        max_withdrawable=withdrawal.youtube_channel.balance * 1000,
    )


@router.get('/lnurl/withdraw-callback', response_class=JSONResponse)
async def withdraw_callback(request: Request, k1: str, pr: str, db=Depends(get_db_session), lnd=Depends(get_lnd)):
    try:
        token = WithdrawalToken.from_jwt(k1)
        withdrawal: WithdrawalDb = await db.query_withdrawal(token.withdrawal_id)
        youtube_channel = withdrawal.youtube_channel
        invoice: LnAddr = lndecode(pr)
        invoice_amount_sats = invoice.amount * 10**8
        min_amount = settings.min_withdraw
        max_amount = youtube_channel.balance
        if invoice_amount_sats < min_amount or invoice_amount_sats > max_amount:
            raise ValidationError(
                f"Invoice amount {invoice_amount_sats} is not in allowed bounds [{min_amount}, {max_amount}]"
            )
        # According to https://github.com/fiatjaf/lnurl-rfc/blob/luds/03.md payment should not block response
        await request.app.task_group.start(partial(
            send_withdrawal,
            youtube_channel_id=youtube_channel.id,
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
    *, youtube_channel_id: UUID, withdrawal_id: UUID, payment_request: PaymentRequest, amount: int, lnd, db,
    task_status: TaskStatus,
):
    message = None
    try:
        async with db.session() as db_session:
            youtube_channel: YoutubeChannel = await db_session.lock_youtube_channel(youtube_channel_id=youtube_channel_id)
            await db_session.lock_withdrawal(withdrawal_id=withdrawal_id)
            if amount > youtube_channel.balance:
                raise ValidationError(
                    f"{youtube_channel!r} balance {youtube_channel.balance} is insufficient (invoiced {amount})"
                )
            task_status.started()
            try:
                await lnd.pay_invoice(payment_request)
            except Exception as exc:
                logger.exception("Failed to send withdrawal payment")
                bugsnag.notify(exc)
                status = 'ERROR'
                message = str(exc)
            else:
                await db_session.withdraw(withdrawal_id=withdrawal_id, youtube_channel_id=youtube_channel_id, amount=amount)
                status = 'OK'
            await db_session.notify(
                f'withdrawal:{youtube_channel_id}',
                Notification(id=youtube_channel_id, status=status, message=message),
            )
    except Exception as exc:
        logger.exception("Internal error in send_withdrawal")
        bugsnag.notify(exc)
        raise


class GoogleAuthState(BaseModel):
    last_url: AnyHttpUrl
    donator_id: UUID


@router.get('/me/youtube/oauth', response_class=JSONResponse)
async def login_via_google(request: Request, donator=Depends(get_donator)):
    aiogoogle = Aiogoogle()
    url = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=request.app.url_path_for('auth_google').make_absolute_url(settings.youtube.oauth.redirect_base_url),
            **settings.youtube.oauth.dict(),
        ),
        state=GoogleAuthState(last_url=request.headers['referer'], donator_id=donator.id).to_jwt(),
    )
    return dict(url=url)


@router.get('/auth-redirect')
async def auth_google(
    request: Request, state: str, error: str = None, error_description: str = None, code: str = None,
    db_session=Depends(get_db_session), donator=Depends(get_donator),
):
    auth_state = GoogleAuthState.from_jwt(state)
    if auth_state.donator_id != donator.id:
        raise ValidationError(
            f"User that initiated Google Auth {donator.id} is not the current user {auth_state.donator_id}, rejecting auth"
        )
    if error:
        return {
            'error': error,
            'error_description': error_description
        }
    elif code:
        try:
            channel_info: ChannelInfo = await fetch_user_channel(request, code)
        except Exception:
            logger.exception("Failed to fetch user's chnanel")
            # TODO: add exception info to last_url hash param and show it using toast
            return RedirectResponse(auth_state.last_url)
        else:
            youtube_channel = YoutubeChannel(
                channel_id=channel_info.id,
                title=channel_info.title,
                thumbnail_url=channel_info.thumbnail,
            )
            await db_session.save_youtube_channel(youtube_channel)
            await db_session.link_youtube_channel(youtube_channel, donator)
            return RedirectResponse(f'/youtube/{youtube_channel.id}')
    else:
        # Should either receive a code or an error
        raise Exception("Something's probably wrong with your callback")


class LoginLnurlResponse(BaseModel):
    lnurl: str


@router.get('/lnauth', response_model=LoginLnurlResponse)
async def login_lnauth(request: Request, donator=Depends(get_donator)):
    url_start = request.app.url_path_for('lnauth_callback').make_absolute_url(settings.lnd.lnurl_base_url)
    query_string = urlencode(dict(
        tag='login',
        k1=donator.id.bytes.hex() * 2,  # k1 size should be 32 bytes
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
        await db_session.login_donator(donator_id, key)
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
async def subscribe(websocket: WebSocket, topic: str, pubsub=Depends(get_pubsub)):
    async def send_to_websocket(msg: str):
        await websocket.send_text(msg)

    await websocket.accept()
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


class YoutubeVideoResponse(BaseModel):
    id: UUID | None
    total_donated: int


@router.get('/youtube-video/{video_id}', response_model=YoutubeVideoResponse)
async def youtube_video_info(video_id: str, db=Depends(get_db_session)):
    try:
        video: YoutubeVideo = await db.query_youtube_video(video_id=video_id)
        return YoutubeVideoResponse(id=video.id, total_donated=video.total_donated)
    except NoResultFound:
        return YoutubeVideoResponse(id=None, total_donated=0)


class OwnershipMessage(BaseModel):
    message: str


@router.get('/me/youtube/ownership-message', response_model=OwnershipMessage)
async def ownership_message(donator=Depends(get_donator)):
    return OwnershipMessage(message=settings.ownership_message.format(donator_id=donator.id))


@router.post('/me/youtube/check-ownership', response_model=list[YoutubeChannel])
async def ownership_check(donator=Depends(get_donator), db=Depends(get_db_session)):
    channel_ids = await find_comment(
        video_id='J2Tz2jGQjHE',
        comment=settings.ownership_message.format(donator_id=donator.id),
    )
    channels = []
    for channel_id in channel_ids:
        youtube_channel = await query_or_fetch_youtube_channel(channel_id, db)
        await db.link_youtube_channel(youtube_channel, donator)
        channels.append(youtube_channel)
    return channels


@router.get("/donatee/recently-donated", response_model=list[YoutubeChannel])
async def recently_donated_donatees(db=Depends(get_db_session)):
    return await db.query_recently_donated_donatees(limit=20)


@router.post("/subscribe-email", response_model=UUID | None)
async def subscribe_email(request: SubscribeEmailRequest, db=Depends(get_db_session)):
    return await db.save_email(request.email)
