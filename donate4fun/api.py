import logging
import math
from uuid import UUID, uuid4
from typing import Callable, Literal
from functools import partial

import bugsnag
from fastapi import APIRouter, WebSocket, Request, Response, Depends, HTTPException
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.datastructures import URL
from pydantic import ValidationError as PydanticValidationError, AnyHttpUrl, Field, AnyUrl
from httpx import HTTPStatusError
from lnurl.models import LnurlResponseModel
from lnurl.types import MilliSatoshi
from lnurl.core import _url_encode as lnurl_encode
from lnpayencode import lndecode, LnAddr
from aiogoogle import Aiogoogle
from anyio.abc import TaskStatus

from .core import get_db_session, get_lnd, get_db, absolute_url_for
from .models import Donation, Donator, Invoice, DonateResponse, DonateRequest, YoutubeChannel, WithdrawalToken, BaseModel
from .types import ValidationError, RequestHash, PaymentRequest
from .youtube import YoutubeDonatee, ChannelInfo, fetch_user_channel, validate_target
from .db import Database, NoResultFound, DonationDb
from .settings import settings

logger = logging.getLogger(__name__)


class CustomRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except HTTPStatusError as exc:
                logger.debug(f"{request.url}: Upstream error", exc_info=exc)
                status_code = exc.response.status_code
                body = exc.response.json()
                return JSONResponse(status_code=500, content={"message": f"Upstream server returned {status_code}: {body}"})
            except (ValidationError, PydanticValidationError) as exc:
                logger.debug(f"{request.url}: Validation error", exc_info=exc)
                return JSONResponse(
                    status_code=400,
                    content={"message": repr(exc)},
                )

        return custom_route_handler


router = APIRouter(route_class=CustomRoute)


def get_donator(request: Request):
    if donator_id := request.session.get('donator'):
        donator = Donator(id=UUID(donator_id))
    else:
        donator = Donator(id=uuid4())
        request.session['donator'] = str(donator.id)
    return donator


def get_youtube_channels(request: Request):
    return request.session.get('youtube_channels', [])


def make_memo(youtube_channel: YoutubeChannel) -> str:
    return f"Donate4.fun to {youtube_channel.title}"


@router.post("/donate", response_model=DonateResponse)
async def donate(
    request: DonateRequest, donator: Donator = Depends(get_donator), db_session=Depends(get_db_session), lnd=Depends(get_lnd),
 ) -> DonateResponse:
    logger.debug(f"Donator {donator.id} wants to donate {request.amount} to {request.target}")
    donatee: YoutubeDonatee = await validate_target(request.target)
    youtube_channel = YoutubeChannel(
        channel_id=donatee.channel.id,
        title=donatee.channel.title,
        thumbnail_url=donatee.channel.thumbnail,
    )
    await db_session.save_youtube_channel(youtube_channel)
    invoice: Invoice = await lnd.create_invoice(memo=make_memo(youtube_channel), value=request.amount)
    donation = Donation(r_hash=invoice.r_hash, amount=invoice.value, youtube_channel=youtube_channel, donator=donator)
    await db_session.create_donation(donation)
    return DonateResponse(donation=donation, payment_request=invoice.payment_request)


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def donation(donation_id: UUID, db_session=Depends(get_db_session), lnd=Depends(get_lnd)):
    donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.lookup_invoice(donation.r_hash)
        if invoice is None or invoice.state == 'CANCELED':
            logger.debug(f"Invoice {invoice} cancelled, recreating")
            invoice = await lnd.create_invoice(memo=make_memo(donation.youtube_channel), value=donation.amount)
            await db_session.update_donation(donation_id=donation_id, r_hash=invoice.r_hash)
        payment_request = invoice.payment_request
    else:
        payment_request = None
    return DonateResponse(donation=donation, payment_request=payment_request)


@router.websocket("/donation/subscribe/{donation_id}")
async def subscribe_to_donation(websocket: WebSocket, donation_id: UUID):
    logger.debug("Connected /donation/subscribe/")
    db: Database = websocket.app.db
    try:
        async with db.pubsub() as sub:
            async for msg in sub.listen_for_donations():
                if msg is None:
                    await websocket.accept()
                    logger.debug(f"Accepted ws connection for {donation_id}")
                elif msg == donation_id:
                    async with db.session() as db_session:
                        donation: Donation = await db_session.query_donation(id=donation_id)
                    if donation.paid_at is not None:
                        await websocket.send_text(donation.json())
                    else:
                        logger.warning(f"Received notification about already paid donation {donation_id}")
                    break
                else:
                    logger.debug(f"Received notification about donation {msg}, skipping")
    except Exception as exc:
        logger.exception("Exception while listening for donations")
        await websocket.send_json(dict(status='error', error=repr(exc)))
    finally:
        await websocket.close()


@router.post("/donation/cancel/{donation_id}")
async def cancel_donation(donation_id: UUID, db=Depends(get_db_session), lnd=Depends(get_lnd)):
    """
    It only works for HODL invoices
    """
    r_hash: RequestHash = await db.cancel_donation(donation_id)
    await lnd.cancel_invoice(r_hash)


@router.get("/donations/latest", response_model=list[Donation])
async def latest_donations(db=Depends(get_db_session)):
    return await db.query_donations(DonationDb.paid_at.isnot(None))


@router.get("/donations/by-donator/{donator_id}", response_model=list[Donation])
async def donator_donations(donator_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations(DonationDb.donator_id == donator_id)


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
    youtube_channels: list[UUID]


@router.get("/donator/me", response_model=MeResponse)
async def me(request: Request, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    try:
        donator = await db.query_donator(donator_id=donator.id)
    except NoResultFound:
        pass
    return MeResponse(donator=donator, youtube_channels=request.session.get('youtube_channels', []))


@router.get("/youtube-channel/{channel_id}", response_model=YoutubeChannel)
async def youtube_channel(channel_id: UUID, db=Depends(get_db_session)):
    return await db.query_youtube_channel(channel_id)


class WithdrawResponse(BaseModel):
    lnurl: str
    amount: int


@router.get('/youtube-channel/{channel_id}/withdraw', response_model=WithdrawResponse)
async def withdraw(request: Request, channel_id: UUID, db_session=Depends(get_db_session)):
    youtube_channels = request.session.get('youtube_channels', [])
    if str(channel_id) not in youtube_channels:
        raise HTTPException(status_code=403, detail="You should prove that you own YouTube channel")
    youtube_channel = await db_session.query_youtube_channel(youtube_channel_id=channel_id)
    if youtube_channel.balance < settings.min_withdraw:
        raise ValidationError(
            f"You can't withdraw less than {settings.min_withdraw}, but available only {youtube_channel.balance}"
        )
    token = WithdrawalToken(
        min_amount=settings.min_withdraw,
        max_amount=youtube_channel.balance,
        description=f'Donate4.Fun withdrawal for "{youtube_channel.title}"',
        youtube_channel_id=youtube_channel.id,
    )
    withdraw_url = URL(absolute_url_for(request, 'lnurl_withdraw')).include_query_params(token=token.to_jwt())
    return WithdrawResponse(
        lnurl=lnurl_encode(str(withdraw_url)),
        amount=youtube_channel.balance,
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
async def lnurl_withdraw(request: Request, token: str):
    decoded = WithdrawalToken.from_jwt(token)
    return LnurlWithdrawResponse(
        callback=absolute_url_for(request, 'withdraw_callback'),
        k1=token,
        default_description=decoded.description,
        min_withdrawable=decoded.min_amount,
        max_withdrawable=decoded.max_amount,
    )


@router.get('/lnurl/callback', response_class=JSONResponse)
async def withdraw_callback(request: Request, k1: str, pr: str, db=Depends(get_db), lnd=Depends(get_lnd)):
    try:
        token = WithdrawalToken.from_jwt(k1)
        invoice: LnAddr = lndecode(pr)
        invoice_amount_sats = invoice.amount * 10**8
        if invoice_amount_sats < token.min_amount or invoice_amount_sats > token.max_amount:
            raise ValidationError(
                f"Invoice amount {invoice_amount_sats} is not in allowed bounds [{token.min_amount}, {token.max_amount}]"
            )
        # According to https://github.com/fiatjaf/lnurl-rfc/blob/luds/03.md payment should not block response
        await request.app.task_group.start(partial(
            send_withdrawal,
            youtube_channel_id=token.youtube_channel_id,
            amount=invoice_amount_sats,
            payment_request=pr,
            lnd=lnd,
            db=db,
        ))
    except Exception as exc:
        return dict(status="ERROR", reason=f"Exception while initiating payment: {type(exc)}({exc})")
    else:
        return dict(status="OK")


async def send_withdrawal(
    *, youtube_channel_id: UUID, payment_request: PaymentRequest, amount: int, lnd, db, task_status: TaskStatus
):
    try:
        async with db.session() as db_session:
            youtube_channel: YoutubeChannel = await db_session.lock_youtube_channel(youtube_channel_id=youtube_channel_id)
            if amount > youtube_channel.balance:
                raise ValidationError(
                    f"{youtube_channel!r} balance {youtube_channel.balance} is insufficient (invoiced {amount})"
                )
            task_status.started()
            await lnd.pay_invoice(payment_request, timeout=settings.withdraw_timeout)
            await db_session.withdraw(youtube_channel_id=youtube_channel_id, amount=amount)
    except Exception as exc:
        logger.exception("Failed to send withdrawal payment")
        bugsnag.notify(exc)
        raise


class GoogleAuthState(BaseModel):
    last_url: AnyHttpUrl
    donator_id: UUID


@router.get('/youtube-channel/{channel_id}/login', response_class=JSONResponse)
async def login_via_google(request: Request, channel_id: UUID, donator=Depends(get_donator)):
    aiogoogle = Aiogoogle()
    url = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=absolute_url_for(request, 'auth_google'),
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
        channel_info: ChannelInfo = await fetch_user_channel(request, code)
        youtube_channel = YoutubeChannel(
            channel_id=channel_info.id,
            title=channel_info.title,
            thumbnail_url=channel_info.thumbnail,
        )
        await db_session.save_youtube_channel(youtube_channel)
        request.session['youtube_channels'] = list(set(request.session.get('youtube_channels', [])) | {str(youtube_channel.id)})
        return RedirectResponse(auth_state.last_url)
    else:
        # Should either receive a code or an error
        raise Exception("Something's probably wrong with your callback")
