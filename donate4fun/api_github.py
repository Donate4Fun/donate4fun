import logging

from furl import furl
from fastapi import APIRouter, Depends, Request

from .core import app
from .api_utils import HttpClient, make_absolute_uri, get_donator
from .models import OAuthResponse, OAuthState, Donator
from .settings import settings
from .types import OAuthError

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/github')


@router.get('/oauth', response_model=OAuthResponse)
async def login_via_github(request: Request, return_to: str, donator=Depends(get_donator)):
    state = OAuthState(
        success_url=make_absolute_uri(return_to),
        error_url=request.headers['referer'],
        donator_id=donator.id,
    )

    params = dict(
        client_id=settings.github.client_id,
        redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='github')),
        state=state.to_jwt(),
        allow_signup=False,
    )
    return OAuthResponse(url=furl('https://github.com/login/oauth/authorize', query_params=params).url)


async def finish_github_oauth(code: str, donator: Donator, request: Request):
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
        print(user_response.json())
