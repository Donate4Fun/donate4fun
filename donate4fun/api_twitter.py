import secrets
import logging
from uuid import UUID

from fastapi import Depends, APIRouter, Request
from furl import furl

from .models import TwitterAccount, Donator, TwitterAccountOwned, OAuthState, OAuthResponse, Toast
from .types import ValidationError, OAuthError, AccountAlreadyLinked, Satoshi
from .api_utils import get_donator, make_absolute_uri, make_redirect, signin_success_message, oauth_success_messages
from .twitter import make_oauth1_client, make_oauth2_client, TwitterApiClient
from .twitter_bot import make_prove_message
from .core import app
from .db_twitter import TwitterDbLib
from .db import db
from .settings import settings

router = APIRouter(prefix='/twitter')
logger = logging.getLogger(__name__)


@router.get("/ownership-message")
async def twitter_ownership_message(me=Depends(get_donator)):
    return dict(message=make_prove_message(me.id))


@router.get('/oauth1', response_model=OAuthResponse)
async def login_via_twitter_oauth1(request: Request, donator=Depends(get_donator)):
    oauth1_ctx = make_oauth1_client(
        oauth=settings.twitter.linking_oauth,
        redirect_uri=make_absolute_uri(request.url_for('oauth1_callback')),
    )
    async with oauth1_ctx as client:
        await client.fetch_request_token('https://api.twitter.com/oauth/request_token')
        auth_url: str = client.create_authorization_url('https://api.twitter.com/oauth/authorize')
        return OAuthResponse(url=auth_url)


@router.get('/oauth1-callback')
async def oauth1_callback(
    request: Request, oauth_token: str = None, oauth_verifier: str = None, denied: str = None, donator=Depends(get_donator),
):
    if denied is not None:
        return make_redirect('settings', [Toast("error", "Authorization denied by user", '')])
    if oauth_token is None or oauth_verifier is None:
        raise ValidationError("oauth_token and oauth_verifier parameters must be present")
    try:
        token = dict(oauth_token=oauth_token, oauth_verifier=oauth_verifier)
        async with make_oauth1_client(oauth=settings.twitter.linking_oauth, token=token) as client:
            token: dict = await client.fetch_access_token('https://api.twitter.com/oauth/access_token', verifier=oauth_verifier)
            client.token = token
            try:
                transferred_amount, linked_account = await login_or_link_twitter_account(client, donator)
            except AccountAlreadyLinked as exc:
                if not donator.connected:
                    linked_account = exc.args[0]
                    request.session['donator'] = str(linked_account.owner_id)
                    request.session['connected'] = True
                    return make_redirect('donator/me', [signin_success_message(linked_account)])
                else:
                    raise OAuthError("Could not link an already linked account") from exc
            else:
                request.session['connected'] = True
                return make_redirect('donator/me', oauth_success_messages(linked_account, transferred_amount))
    except OAuthError as exc:
        logger.exception("OAuth error")
        return make_redirect('settings', [Toast("error", exc.args[0], exc.__cause__)])


@router.get('/oauth', response_model=OAuthResponse)
async def login_via_twitter(request: Request, return_to: str, expected_account: UUID | None = None, donator=Depends(get_donator)):
    code_verifier = secrets.token_urlsafe(32)
    state = OAuthState(
        success_path=return_to,
        error_path=str(furl(request.headers['referer']).path),
        donator_id=donator.id,
        code_verifier=code_verifier,
        expected_account=expected_account,
    )
    encrypted_state = state.to_jwt()
    if len(encrypted_state) > 500:
        raise ValidationError(f"State is too long for Twitter: {len(encrypted_state)} chars")
    async with make_link_oauth2_client() as client:
        url, state = client.create_authorization_url(
            url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
            state=encrypted_state,
        )
        return OAuthResponse(url=url)


async def finish_twitter_oauth(code: str, donator: Donator, code_verifier: str) -> tuple[Satoshi, TwitterAccountOwned]:
    async with make_link_oauth2_client() as client:
        try:
            token: dict = await client.fetch_token(code=code, code_verifier=code_verifier)
        except Exception as exc:
            raise OAuthError("Failed to fetch OAuth token") from exc
        client.token = token
        return await login_or_link_twitter_account(client, donator)


async def login_or_link_twitter_account(client, donator: Donator) -> tuple[Satoshi, TwitterAccountOwned]:
    try:
        account: TwitterAccount = await TwitterApiClient(client).get_me()
    except Exception as exc:
        raise OAuthError("Failed to fetch user's account") from exc

    try:
        async with db.session() as db_session:
            twitter_db = TwitterDbLib(db_session)
            await twitter_db.save_account(account)
            owned_account: TwitterAccountOwned = await twitter_db.query_account(user_id=account.user_id)
            if not owned_account.via_oauth:
                await twitter_db.link_account(account, donator, via_oauth=True)
                return await twitter_db.transfer_donations(account, donator), owned_account
    except Exception as exc:
        raise OAuthError("Failed to link account") from exc
    else:
        raise AccountAlreadyLinked(owned_account)


def make_link_oauth2_client(token=None):
    """
    This client is used to link Twitter account to donator (OAuth2 flow)
    """
    return make_oauth2_client(
        settings.twitter.linking_oauth,
        scope='tweet.read users.read',
        token=token,
        redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='twitter')),
    )
