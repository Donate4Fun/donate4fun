import logging
import asyncio
import re
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial
from io import BytesIO
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client, AsyncOAuth2Client

from .db import db
from .db_twitter import TwitterDbLib
from .models import TwitterAccount
from .types import ValidationError
from .settings import settings, TwitterOAuth
from .api_utils import scrape_lightning_address, register_app_command

logger = logging.getLogger(__name__)


class APIError(Exception):
    pass


MediaID = int
TwitterHandle = str


class UnsupportedTwitterUrl(ValidationError):
    pass


class InvalidResponse(Exception):
    pass


def parse_twitter_profile_url(url: str) -> str:
    """
    Returns Twitter handle (username) if matches
    """
    if match := re.match(r'^https:\/\/twitter.com\/(?!home|messages|notifications|settings)i(?<username>([a-zA-Z0-9_]{4,15})($|\/.*)', url):  # noqa
        return match.groups('username')


class TwitterApiClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client: httpx.AsyncClient = client
        self.get = partial(self.request, 'GET')
        self.post = partial(self.request, 'POST')

    async def request_raw(self, method: str, api_path: str, **kwargs) -> httpx.Response:
        response = await self.client.request(
            method=method,
            url=api_path,
            **kwargs
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if self.is_json_content_type(exc.response):
                body = exc.response.json()
            else:
                body = exc.response.content
            raise APIError(body if body else exc.response.status_code) from exc
        return response

    def is_json_content_type(self, response):
        return response.headers.get('content-type', '').split(';', 1)[0] == 'application/json'

    async def request(self, method: str, api_path: str, **kwargs) -> dict[str, Any] | bytes:
        response = await self.request_raw(method, api_path, **kwargs)
        if response.status_code == 204:
            return
        elif self.is_json_content_type(response):
            return response.json()
        else:
            return response.content

    @asynccontextmanager
    async def stream(self, method: str, api_path: str, **kwargs):
        async with self.client.stream(method, api_path, **kwargs) as response:
            yield response

    async def get_pages(self, api_path: str, limit: int, params: dict[str, Any], **kwargs) -> list[Any]:
        results = []
        params_ = params.copy()
        while True:
            response = await self.request_raw('GET', api_path, params=params_, **kwargs)
            if response.status_code == 204:
                break
            elif response.headers['content-type'].split(';', 1)[0] == 'application/json':
                data = response.json()
                results.extend(data.get('data', []))
                if len(results) < limit:
                    params_['pagination_token'] = data['meta']['next_token']
                else:
                    break
            else:
                raise InvalidResponse
        return results

    async def get_user_by(self, handle: str | None = None, user_id: int | None = None) -> TwitterAccount:
        if handle is not None:
            path = f'/users/by/username/{handle}'
        elif user_id is not None:
            path = f'/users/{user_id}'
        else:
            raise ValueError("One of handle or user_id should be provided")
        data: dict = await self.get(path, params={'user.fields': get_user_fields()})
        return api_data_to_twitter_account(data['data'])

    async def get_me(self) -> TwitterAccount:
        data: dict = await self.get('/users/me', params={'user.fields': get_user_fields()})
        return api_data_to_twitter_account(data['data'])

    async def upload_media(self, image: bytes, mime_type: str, category: str) -> MediaID:
        upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        params = dict(
            command='INIT',
            total_bytes=len(image),
            media_type=mime_type,
            media_category=category,
        )
        media_info = await self.post(upload_url, params=params)
        media_id = media_info['media_id']
        await self.post(
            upload_url,
            data=dict(
                command='APPEND',
                media_id=media_id,
                segment_index=0,
            ),
            files=dict(media=('image', BytesIO(image), mime_type)),
        )
        state_response = await self.post(
            upload_url,
            params=dict(
                command='FINALIZE',
                media_id=media_id,
            ),
        )
        if 'processing_info' in state_response:
            while True:
                info = state_response['processing_info']
                if info['state'] == 'succeeded':
                    break
                check_after_secs = info['check_after_secs']
                logger.debug("upload_media: state is %s, sleeping for %d seconds", info, check_after_secs)
                await asyncio.sleep(check_after_secs)
                state_response = await self.post(upload_url, params=dict(
                    command='STATUS',
                    media_id=media_id,
                ))
        logger.trace("Media uploaded: %s", state_response)
        return media_id


@register_app_command
async def fetch_and_save_twitter_account(handle: str):
    async with db.session() as db_session, make_apponly_client(token=settings.twitter.linking_oauth.bearer_token) as client:
        account: TwitterAccount = await TwitterApiClient(client).get_user_by(handle=handle)
        await db_session.save_twitter_account(account)


class OAuthTokenLoader:
    def __init__(self, name: str):
        self.name = name

    @property
    def settings(self):
        return self.settings_getter()

    async def load(self) -> dict:
        async with db.session() as db_session:
            return await TwitterDbLib(db_session).query_oauth_token(self.name)

    async def save(self, token: dict):
        async with db.session() as db_session:
            await TwitterDbLib(db_session).save_oauth_token(self.name, token)


@asynccontextmanager
async def make_oauth2_client(oauth: TwitterOAuth, scope: str, token: dict | None = None, update_token=None, redirect_uri=None):
    async with AsyncOAuth2Client(
        client_id=oauth.client_id,
        client_secret=oauth.client_secret,
        scope=scope,
        token_endpoint='https://api.twitter.com/2/oauth2/token',
        redirect_uri=redirect_uri,
        code_challenge_method='S256',
        token=token,
        update_token=update_token,
        base_url='https://api.twitter.com/2',
    ) as client:
        yield client


@asynccontextmanager
async def make_oauth1_client(oauth: TwitterOAuth, token: dict | None = None, **kwargs):
    async with AsyncOAuth1Client(
        client_id=oauth.consumer_key,
        client_secret=oauth.consumer_secret,
        base_url='https://api.twitter.com/2',
        **kwargs,
    ) as client:
        if token:
            client.token = token
        yield client


@asynccontextmanager
async def make_apponly_client(token: str):
    async with httpx.AsyncClient(
        headers=dict(authorization=f'Bearer {token}'),
        base_url='https://api.twitter.com/2',
    ) as client:
        yield client


def get_user_fields():
    return 'id,name,profile_image_url,description,verified,entities'


def api_data_to_twitter_account(data: dict):
    return TwitterAccount(
        user_id=int(data['id']),
        handle=data['username'],
        name=data['name'],
        profile_image_url=data['profile_image_url'],
        lightning_address=scrape_lightning_address(data['description']),
        last_fetched_at=datetime.utcnow(),
    )


@register_app_command
async def get_profile_banner():
    """
    Does it work?
    """
    async with db.session() as db_session:
        token: dict = await db_session.query_oauth_token('twitter_oauth1')
    async with make_oauth1_client() as client:
        client.token = token
        url = 'https://api.twitter.com/1.1/users/profile_banner.json'
        try:
            response = await client.get(url, params=dict(screen_name='elonmusk'))
        except httpx.HTTPStatusError as exc:
            auth_header = exc.request.headers['authorization']
            logger.exception("Failed to get banner image:\n%s\n%s\n%s", auth_header, exc.request.headers, exc.response.json())
        else:
            print(response.json())
