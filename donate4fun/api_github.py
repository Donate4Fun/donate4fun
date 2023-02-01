import logging

from furl import furl
from fastapi import APIRouter, Depends, Request

from .core import app
from .api_utils import HttpClient, make_absolute_uri, get_donator
from .models import OAuthResponse, OAuthState, Donator, GithubUser, GithubUserOwned
from .settings import settings
from .types import OAuthError, AccountAlreadyLinked, Satoshi
from .db import db
from .db_github import GithubDbLib

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/github')


@router.get('/oauth', response_model=OAuthResponse)
async def login_via_github(request: Request, return_to: str, donator=Depends(get_donator)):
    state = OAuthState(
        success_path=return_to,
        error_path=str(furl(request.headers['referer']).path),
        donator_id=donator.id,
    )

    params = dict(
        client_id=settings.github.client_id,
        redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='github')),
        state=state.to_jwt(),
        allow_signup=False,
    )
    return OAuthResponse(url=furl('https://github.com/login/oauth/authorize', query_params=params).url)


async def finish_github_oauth(code: str, donator: Donator) -> Satoshi:
    async with HttpClient(headers={'Accept': 'application/json'}) as client:
        params = dict(
            client_id=settings.github.client_id,
            client_secret=settings.github.client_secret,
            code=code,
            redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='github')),
        )
        token_response = await client.post('https://github.com/login/oauth/access_token', json=params)
        token: dict = token_response.json()
        if 'error' in token:
            raise OAuthError(token['error'], f"{token['error_description']} ({token['error_uri']})")
        access_token = token['access_token']
        user_response = await client.get('https://api.github.com/user', headers={'Authorization': f'Bearer {access_token}'})
        data = user_response.json()
        github_user = GithubUser(
            user_id=data['id'],
            avatar_url=data['avatar_url'],
            name=data['name'],
            login=data['login'],
        )
        return await login_or_link_github_user(github_user, donator)


async def login_or_link_github_user(account: GithubUser, donator: Donator) -> Satoshi:
    try:
        async with db.session() as db_session:
            github_db = GithubDbLib(db_session)
            await github_db.save_account(account)
            owned_account: GithubUserOwned = await github_db.query_account(user_id=account.user_id)
            if not owned_account.via_oauth:
                await github_db.link_account(account, donator, via_oauth=True)
                return await github_db.transfer_donations(account, donator)
    except Exception as exc:
        raise OAuthError("Failed to link account") from exc
    else:
        raise AccountAlreadyLinked(owned_account.owner_id)
