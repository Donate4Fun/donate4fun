import secrets
import logging

from fastapi import Depends, APIRouter, Request
from fastapi.responses import RedirectResponse

from .models import TwitterAccount, Donator, TwitterAccountOwned, OAuthState, OAuthResponse
from .types import ValidationError, OAuthError
from .api_utils import get_donator, make_absolute_uri, error_redirect
from .twitter import make_prove_message, make_link_oauth2_client, make_oauth1_client, fetch_twitter_me
from .db_twitter import TwitterDbLib
from .db import db

router = APIRouter(prefix='/twitter')
logger = logging.getLogger(__name__)


@router.get("/ownership-message")
async def twitter_ownership_message(me=Depends(get_donator)):
    return dict(message=make_prove_message(me.id))


@router.get('/oauth1', response_model=OAuthResponse)
async def login_via_twitter_oauth1(request: Request, donator=Depends(get_donator)):
    async with make_oauth1_client(redirect_uri=make_absolute_uri(request.url_for('oauth1_callback'))) as client:
        await client.fetch_request_token('https://api.twitter.com/oauth/request_token')
        auth_url: str = client.create_authorization_url('https://api.twitter.com/oauth/authorize')
        return OAuthResponse(url=auth_url)


@router.get('/oauth1-callback')
async def oauth1_callback(
    request: Request, oauth_token: str = None, oauth_verifier: str = None, denied: str = None, donator=Depends(get_donator),
):
    if denied is not None:
        return error_redirect(make_absolute_uri('settings'), "Authorization denied by user", '')
    try:
        async with make_oauth1_client(token=oauth_token) as client:
            token: dict = await client.fetch_access_token('https://api.twitter.com/oauth/access_token', verifier=oauth_verifier)
            client.token = token
            await login_or_link_twitter_account(client, donator, request)
            return RedirectResponse(make_absolute_uri('donator/me'))
    except OAuthError as exc:
        logger.exception("OAuth error")
        return error_redirect(make_absolute_uri('settings'), exc.args[0], exc.__cause__)


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


async def finish_twitter_oauth(code: str, donator: Donator, request: Request, code_verifier: str):
    async with make_link_oauth2_client() as client:
        try:
            token: dict = await client.fetch_token(code=code, code_verifier=code_verifier)
        except Exception as exc:
            raise OAuthError("Failed to fetch OAuth token") from exc
        client.token = token
        await login_or_link_twitter_account(client, donator, request)


async def login_or_link_twitter_account(client, donator: Donator, request):
    try:
        account: TwitterAccount = await fetch_twitter_me(client)
    except Exception as exc:
        raise OAuthError("Failed to fetch user's account") from exc

    try:
        async with db.session() as db_session:
            twitter_db = TwitterDbLib(db_session)
            await twitter_db.save_account(account)
            owned_account: TwitterAccountOwned = await twitter_db.query_account(user_id=account.user_id)
            if owned_account.via_oauth:
                if donator.connected:
                    raise OAuthError("Could not link already linked account")
                request.session['donator'] = str(owned_account.owner_id)
            else:
                await twitter_db.link_account(account, donator, via_oauth=True)
                await twitter_db.transfer_donations(account, donator)
            request.session['connected'] = True
    except Exception as exc:
        raise OAuthError("Failed to link account") from exc
