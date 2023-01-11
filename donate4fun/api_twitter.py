import secrets
import logging
from uuid import UUID

import posthog
from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from furl import furl

from .models import TwitterAccount, TransferResponse, Donator, TwitterAccountOwned, Donation, OAuthState, OAuthResponse
from .types import ValidationError
from .api_utils import get_donator, load_donator, get_db_session, make_absolute_uri
from .twitter import make_prove_message, make_link_oauth2_client, make_oauth1_client, fetch_twitter_me
from .db_models import DonationDb
from .db import db

router = APIRouter(prefix='/twitter')
logger = logging.getLogger(__name__)


class TwitterAccountResponse(TwitterAccount):
    is_my: bool


@router.get("/account/{account_id}", response_model=TwitterAccountResponse)
async def twitter_account(account_id: UUID, db=Depends(get_db_session), me=Depends(get_donator)):
    account: TwitterAccountOwned = await db.query_twitter_account(id=account_id, owner_id=me.id)
    return TwitterAccountResponse(
        **account.dict(),
        is_my=account.owner_id == me.id,
    )


@router.get("/linked", response_model=list[TwitterAccountOwned])
async def my_linked_twitter_accounts(db=Depends(get_db_session), me=Depends(get_donator)):
    return await db.query_donator_twitter_accounts(me.id)


@router.get("/ownership-message")
async def twitter_ownership_message(me=Depends(get_donator)):
    return dict(message=make_prove_message(me.id))


@router.post('/account/{account_id}/transfer', response_model=TransferResponse)
async def twitter_account_transfer(account_id: UUID, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    account: TwitterAccountOwned = await db.query_twitter_account(id=account_id, owner_id=donator.id)
    if not account.owner_id == donator.id:
        raise HTTPException(status_code=401, detail="You should prove that you own Twitter accoutn")
    if not donator.connected:
        raise ValidationError("You should have a connected auth method to claim donations")
    if account.balance != 0:
        amount = await db.transfer_twitter_donations(twitter_account=account, donator=donator)
    posthog.capture(donator.id, 'transfer', dict(source='twitter', amount=amount))
    return TransferResponse(amount=amount)


@router.get("/account/{account_id}/donations/by-donatee", response_model=list[Donation])
async def donatee_donations(account_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations((DonationDb.twitter_account_id == account_id) & DonationDb.paid_at.isnot(None))


class OAuthError(Exception):
    pass


def error_response(url: str, title: str, message: str):
    return RedirectResponse(furl(url).set(dict(error=title, message=str(message))).url)


@router.get('/oauth', response_model=OAuthResponse)
async def login_via_twitter(request: Request, return_to: str, donator=Depends(get_donator)):
    async with make_link_oauth2_client() as client:
        code_verifier = secrets.token_urlsafe(32)
        state = OAuthState(
            success_url=make_absolute_uri(return_to),
            error_url=request.headers['referer'],
            donator_id=donator.id,
            code_verifier=code_verifier,
        )
        encrypted_state = state.to_jwt()
        if len(encrypted_state) > 500:
            raise ValidationError("State is too long for Twitter: %d chars", len(encrypted_state))
        url, state = client.create_authorization_url(
            url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
            state=encrypted_state,
        )
        return OAuthResponse(url=url)


@router.get('/oauth-redirect')
async def auth_redirect(
    request: Request, state: str, error: str = None, error_description: str = None, code: str = None,
    donator=Depends(get_donator),
):
    auth_state = OAuthState.from_jwt(state)
    if auth_state.donator_id != donator.id:
        raise ValidationError(
            f"User that initiated Google Auth {donator.id} is not the current user {auth_state.donator_id}, rejecting auth"
        )

    try:
        if error:
            raise OAuthError("OAuth error", error)
        elif code:
            async with make_link_oauth2_client() as client:
                try:
                    token: dict = await client.fetch_token(code=code, code_verifier=auth_state.code_verifier)
                except Exception as exc:
                    raise OAuthError("Failed to fetch OAuth token") from exc
                client.token = token
                await login_or_link_twitter_account(client, donator, request)
                return RedirectResponse(auth_state.success_url)
        else:
            # Should either receive a code or an error
            raise ValidationError("Something's probably wrong with your callback")
    except OAuthError as exc:
        logger.exception("OAuth error")
        return error_response(auth_state.error_url, exc.args[0], exc.__cause__)


async def login_or_link_twitter_account(client, donator: Donator, request):
    try:
        account: TwitterAccount = await fetch_twitter_me(client)
    except Exception as exc:
        raise OAuthError("Failed to fetch user's account") from exc

    try:
        async with db.session() as db_session:
            await db_session.save_twitter_account(account)
            owned_account: TwitterAccountOwned = await db_session.query_twitter_account(user_id=account.user_id)
            if owned_account.via_oauth:
                if donator.connected:
                    raise OAuthError("Could not link already linked account")
                request.session['donator'] = str(owned_account.owner_id)
            else:
                await db_session.link_twitter_account(account, donator, via_oauth=True)
            request.session['connected'] = True
    except Exception as exc:
        raise OAuthError("Failed to link account") from exc


@router.post("/account/{account_id}/unlink")
async def unlink_twitter_account(account_id: UUID, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    await db.unlink_twitter_account(account_id=account_id, owner_id=me.id)
    me = await db.query_donator(id=me.id)
    if not me.connected and me.balance > 0:
        raise ValidationError("Unable to unlink last auth method having a positive balance")
