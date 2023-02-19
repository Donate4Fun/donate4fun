import logging
from uuid import UUID
from functools import partial
from urllib.parse import urlencode

import ecdsa
import posthog
from fastapi import FastAPI, WebSocket, Request, Depends, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse
from lnurl.core import _url_encode as lnurl_encode
from lnpayencode import LnAddr
from anyio.abc import TaskStatus
from rollbar.contrib.fastapi.routing import RollbarLoggingRoute
from starlette.datastructures import URL
from httpx import HTTPStatusError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm.exc import NoResultFound
from jwt import InvalidTokenError

from .models import (
    Donation, Donator, Invoice, SocialAccount,
    WithdrawalToken, BaseModel, Notification, Credentials, SubscribeEmailRequest,
    DonatorStats, PayInvoiceResult, Donatee, OAuthState, Toast, SocialProviderId,
)
from .types import ValidationError, PaymentRequest, OAuthError, LnurlpError, AccountAlreadyLinked
from .core import to_base64
from .db_models import WithdrawalDb
from .db_libs import WithdrawalDbLib, DonationsDbLib, OtherDbLib
from .settings import settings
from .social import SocialProvider
from .api_utils import (
    get_donator, load_donator, get_db_session, task_group, only_me, make_redirect, get_donations_db, sha256hash,
    oauth_success_messages, signin_success_message,
)
from .lnd import PayInvoiceError, LnurlWithdrawResponse, lnd, lightning_payment_metadata, LndIsNotReady
from .pubsub import pubsub
from . import api_twitter, api_youtube, api_github, api_social, api_donation


logger = logging.getLogger(__name__)
router = app = FastAPI()
router.route_class = RollbarLoggingRoute
app.include_router(api_twitter.router)
app.include_router(api_youtube.router)
app.include_router(api_youtube.legacy_router)
app.include_router(api_github.router)
app.include_router(api_social.router)
app.include_router(api_donation.router)


@router.exception_handler(LnurlpError)
def lnurlp_error_handler(request, exc):
    return JSONResponse(status_code=503, content={"message": f"Failed to communicate with a Lightning Address provider: {exc}"})


@app.exception_handler(HTTPStatusError)
def http_status_error_handler(request, exc):
    logger.debug(f"{request.url}: Upstream error", exc_info=exc)
    status_code = exc.response.status_code
    if 'application/json' in exc.response.headers.get('content-type', ''):
        body = exc.response.json()
    else:
        body = exc.response.text
    return JSONResponse(status_code=500, content={"message": f"Upstream server returned {status_code}: {body}"})


@app.exception_handler(LndIsNotReady)
def lnd_is_not_ready_handler(request, exc):
    info: dict = exc.args[0]
    synced_to_chain: bool = info['synced_to_chain']
    synced_to_graph: bool = info['synced_to_graph']
    return JSONResponse(status_code=503, content=dict(
        message=f"Lightning node is not ready: synced_to_chain={synced_to_chain} synced_to_graph={synced_to_graph}"
    ))


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
async def donator_stats(request: Request, donator_id: UUID, db=Depends(get_donations_db), me=Depends(only_me)):
    return await db.query_donator_stats(donator_id)


@router.get('/lnurl/withdraw', response_model=LnurlWithdrawResponse)
async def lnurl_withdraw(request: Request, token: str, db=Depends(get_db_session)):
    decoded = WithdrawalToken.from_jwt(token)
    withdrawal: WithdrawalDb = await WithdrawalDbLib(db).query_withdrawal(decoded.withdrawal_id)
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
        withdrawal: WithdrawalDb = await WithdrawalDbLib(db).query_withdrawal(token.withdrawal_id)
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
            donator_id=donator.id,
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


class WithdrawWithInvoiceRequest(BaseModel):
    invoice: PaymentRequest


@router.post('/me/withdraw')
async def withdraw_with_invoice(request: WithdrawWithInvoiceRequest, me=Depends(only_me)):
    pass


class PaymentCallbackResponse(BaseModel):
    status: str
    pr: PaymentRequest


@router.get('/lnurl/{provider_id}/{receiver_id}/payment-callback', response_model=PaymentCallbackResponse)
async def payment_callback(
    request: Request, provider_id: SocialProviderId, receiver_id: UUID, amount: int = Query(...), comment: str = Query(...),
    db_session=Depends(get_db_session),
):
    """
    This callback is needed for lightning address support.
    """
    provider = SocialProvider.create(provider_id)
    receiver: SocialAccount | Donator = await provider.wrap_db(db_session).query_account(id=receiver_id)
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
    await DonationsDbLib(db_session).create_donation(donation)
    return PaymentCallbackResponse(
        status='OK',
        pr=invoice.payment_request,
    )


async def send_withdrawal(
    *, donator_id: UUID, withdrawal_id: UUID, payment_request: PaymentRequest, amount: int, lnd, db,
    task_status: TaskStatus,
):
    try:
        async with db.session() as db_session:
            withdrawal_db = WithdrawalDbLib(db_session)
            await withdrawal_db.start_withdraw(withdrawal_id=withdrawal_id, amount=amount, fee_msat=settings.fee_limit * 1000)
            task_status.started()
            result: PayInvoiceResult = await lnd.pay_invoice(payment_request)
            await withdrawal_db.finish_withdraw(withdrawal_id=withdrawal_id, fee_msat=result.fee_msat)
    except PayInvoiceError as exc:
        logger.exception("Failed to send withdrawal payment")
        params = dict(amount=amount, withdrawal_id=withdrawal_id, message=str(exc))
        posthog.capture(donator_id, 'withdraw-error-payinvoice', params)
        async with db.session() as db_session:
            await db_session.notify(
                f'withdrawal:{withdrawal_id}',
                Notification(id=withdrawal_id, status='ERROR', message=str(exc)),
            )
    except Exception as exc:
        logger.exception("Internal error in send_withdrawal")
        posthog.capture(donator_id, 'withdraw-error', dict(amount=amount, withdrawal_id=withdrawal_id, message=str(exc)))
        raise
    else:
        posthog.capture(donator_id, 'withdraw', dict(amount=amount, withdrawal_id=withdrawal_id))


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
        posthog.identify(credentials.donator, dict(pubkey=credentials.lnauth_pubkey))
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
    return await OtherDbLib(db).query_recently_donated_donatees(limit=20)


@router.post("/subscribe-email", response_model=UUID | None)
async def subscribe_email(request: SubscribeEmailRequest, db=Depends(get_db_session), me=Depends(get_donator)):
    subscription_id: UUID = await OtherDbLib(db).save_email(request.email)
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
    withdrawal: WithdrawalDb = await WithdrawalDbLib(db).create_withdrawal(donator=me)
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


@router.get('/oauth-redirect/{provider}')
async def oauth_redirect(
    request: Request, provider: SocialProviderId, state: str, error: str = None, error_description: str = None, code: str = None,
    donator=Depends(get_donator),
):
    try:
        try:
            auth_state = OAuthState.from_jwt(state)
        except InvalidTokenError as exc:
            error_path = '/'
            raise OAuthError("Can't deserialize state") from exc
        else:
            error_path = auth_state.error_path
        if auth_state.donator_id != donator.id:
            raise ValidationError(
                f"User that initiated Google Auth {donator.id} is not the current user {auth_state.donator_id}, rejecting auth"
            )
        if error:
            raise OAuthError("OAuth error", error)
        elif code:
            try:
                if provider == 'twitter':
                    transferred_amount, linked_account = await api_twitter.finish_twitter_oauth(
                        code, donator, auth_state.code_verifier,
                    )
                elif provider == 'youtube':
                    transferred_amount, linked_account = await api_youtube.finish_youtube_oauth(code, donator)
                elif provider == 'github':
                    transferred_amount, linked_account = await api_github.finish_github_oauth(code, donator)
            except AccountAlreadyLinked as exc:
                if auth_state.allow_sign_in:
                    linked_account = exc.args[0]
                    request.session['donator'] = str(linked_account.owner_id)
                    request.session['connected'] = True
                    return make_redirect(auth_state.success_path, [signin_success_message(linked_account)])
                else:
                    raise OAuthError("Could not link an already linked account") from exc
            else:
                request.session['connected'] = True
                return make_redirect(auth_state.success_path, oauth_success_messages(linked_account, transferred_amount))
        else:
            # Should either receive a code or an error
            raise ValidationError("Something is probably wrong with your callback")
    except OAuthError as exc:
        logger.exception("OAuth error")
        message = '\n'.join(exc.args[1:])
        if exc.__cause__:
            message += '\n' + str(exc.__cause__)
        return make_redirect(error_path, [Toast('error', exc.args[0], message)])


@router.get("/donatees/top-unclaimed", response_model=list[Donatee])
async def donatees_list(db=Depends(get_db_session), limit: int = 20, offset: int = 0):
    return await OtherDbLib(db).query_top_unclaimed_donatees(limit=limit, offset=offset)
