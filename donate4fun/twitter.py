import asyncio
import json
import logging
import re
import secrets
import importlib
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from functools import partial
from io import BytesIO
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client, AsyncOAuth2Client

from .db import db
from .db_other import OAuthDbLib
from .models import TwitterAccount
from .types import Url
from .settings import TwitterOAuth
from .api_utils import scrape_lightning_address, register_app_command, HttpClient
from .twitter_models import APIError, InvalidResponse, MediaID, TweetId, Tweet, TwitterHandle, OAuth1Token

logger = logging.getLogger(__name__)


def parse_twitter_profile_url(url: str) -> str:
    """
    Returns Twitter handle (username) if matches
    """
    if match := re.match(r'^https:\/\/twitter.com\/(?!home|messages|notifications|settings)i(?<username>([a-zA-Z0-9_]{4,15})($|\/.*)', url):  # noqa
        return match.groups('username')


class TwitterApiClient:
    DEFAULT_TWEET_FIELDS = (
        'created_at,attachments,author_id,context_annotations,conversation_id,'
        'entities,source,text,referenced_tweets,id,in_reply_to_user_id'
    )

    def __init__(self, client: httpx.AsyncClient):
        self.client: httpx.AsyncClient = client
        self.get = partial(self.request, 'GET')
        self.post = partial(self.request, 'POST')
        self.delete = partial(self.request, 'DELETE')

    @classmethod
    @asynccontextmanager
    async def create_oauth2(
        cls, oauth: TwitterOAuth, scope: str, token: OAuth1Token | None = None, update_token=None, redirect_uri=None,
    ) -> AsyncIterator['TwitterApiClient']:
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
            client_kwargs=dict(transport=httpx.HTTPTransport(retries=3)),
        ) as client:
            yield cls(client)

    @classmethod
    @asynccontextmanager
    async def create_oauth1(cls, oauth: TwitterOAuth, token: dict | None = None, **kwargs) -> AsyncIterator['TwitterApiClient']:
        async with AsyncOAuth1Client(
            client_id=oauth.consumer_key,
            client_secret=oauth.consumer_secret,
            base_url='https://api.twitter.com/2',
            client_kwargs=dict(transport=httpx.HTTPTransport(retries=3)),
            **kwargs,
        ) as client:
            if token:
                client.token = token
            yield cls(client)

    @classmethod
    @asynccontextmanager
    async def create_apponly(cls, token: str):
        async with httpx.AsyncClient(
            headers=dict(authorization=f'Bearer {token}'),
            base_url='https://api.twitter.com/2',
        ) as client:
            yield cls(client)

    async def request_raw(self, method: str, api_path: str, **kwargs) -> httpx.Response:
        response = await self.client.request(
            method=method,
            url=api_path,
            **kwargs
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self.handle_http_status_error(exc)
        return response

    def handle_http_status_error(self, exc: httpx.HTTPStatusError):
        if self.is_json_content_type(exc.response):
            body = exc.response.json()
            message = body.get('detail') or json.dumps(body)
        else:
            body = message = exc.response.content
        raise APIError(message=message, status_code=exc.response.status_code, body=body) from exc

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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                # Read the body before closing .stream() context
                await response.aread()
                self.handle_http_status_error(exc)
            yield response

    async def get_pages(self, api_path: str, params: dict, **kwargs) -> AsyncIterator[dict]:
        """
        Iterates over pages of data. It expects that response is a list of items in 'data' field.
        """
        params_ = params.copy()
        while True:
            data: dict = await self.request('GET', api_path, params=params_, **kwargs)
            if not isinstance(data, dict):
                raise InvalidResponse
            items = data.get('data', [])
            if len(items) == 0:
                break
            for item in items:
                yield item
            params_['pagination_token'] = data['meta']['next_token']

    @classmethod
    async def fetch_access_token(self, oauth_token: str, oauth_verifier: str) -> OAuth1Token:
        """
        According to https://developer.twitter.com/en/docs/authentication/api-reference/access_token
        this API does not require auth, so we use plain httpx.AsyncClient
        """
        async with HttpClient() as client:
            try:
                resp = await client.post(
                    'https://api.twitter.com/oauth/access_token',
                    params=dict(
                        oauth_token=oauth_token,
                        oauth_verifier=oauth_verifier,
                    ),
                )
            except httpx.HTTPStatusError as exc:
                raise APIError(
                    "Failed to fetch access token",
                    body=exc.response.text,
                    status_code=exc.response.status_code,
                ) from exc
            return AsyncOAuth1Client(client_id='junk').parse_response_token(resp.status_code, resp.text)

    async def fetch_token(self, code: str, code_verifier: str):
        token: dict = await self.client.fetch_token(code=code, code_verifier=code_verifier)
        self.client.token = token

    def create_authorization_url(self, code_verifier: str, state: str):
        url, state = self.client.create_authorization_url(
            url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
            state=state,
        )
        return url

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

    async def get_profile_banner(self, screen_name: str) -> dict:
        url = 'https://api.twitter.com/1.1/users/profile_banner.json'
        data: dict = await self.get(url, params=dict(screen_name=screen_name))
        # FIXME: parse data
        return data

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

    async def send_tweet(self, reply_to: TweetId = None, text: str = None, media_id: int = None) -> Tweet:
        body = {}
        if reply_to is not None:
            body['reply'] = dict(in_reply_to_tweet_id=str(reply_to))
        if text is not None:
            body['text'] = text
        if media_id is not None:
            body['media'] = dict(media_ids=[str(media_id)])
        data = await self.post('/tweets', json=body)
        tweet = Tweet(**data['data'])
        logger.trace("tweeted https://twitter.com/status/%s: %s", tweet.id, tweet.text)
        return tweet

    async def search_recent_tweets(self, query: str) -> AsyncIterator[Tweet]:
        async for tweet in self.get_pages('/tweets/search/recent', params=dict(query=query)):
            yield Tweet(**tweet)

    def get_tweets_by_user(self, *, handle: TwitterHandle) -> AsyncIterator[Tweet]:
        return self.search_recent_tweets(query=f'from:{handle}')

    def get_replies(self, *, tweet_id: TweetId) -> AsyncIterator[Tweet]:
        return self.search_recent_tweets(query=f'in_reply_to_tweet_id:{tweet_id}')

    @asynccontextmanager
    async def stream_tweets(self, query: str) -> AsyncIterator[AsyncIterator[Tweet]]:
        current_rules: list = (await self.get('/tweets/search/stream/rules')).get('data', [])
        logger.debug("current rules: %s", current_rules)
        expected_rules = [dict(value=query)]
        if [dict(value=rule['value']) for rule in current_rules] != expected_rules:
            logger.debug("current rules differ with expected, overriding with %s", expected_rules)
            if current_rules:
                current_rule_ids = [rule['id'] for rule in current_rules]
                await self.post('/tweets/search/stream/rules', json=dict(
                    delete=dict(ids=current_rule_ids)
                ))
            await self.post('/tweets/search/stream/rules', json=dict(
                add=expected_rules,
            ))
        params = {
            'tweet.fields': self.DEFAULT_TWEET_FIELDS,
            'expansions': 'author_id,referenced_tweets.id,in_reply_to_user_id,referenced_tweets.id.author_id',
        }
        async with self.stream('GET', '/tweets/search/stream', params=params, timeout=3600) as response:
            yield self.generate_tweets(response)

    async def generate_tweets(self, response: httpx.Response) -> AsyncIterator[Tweet]:
        async for chunk in response.aiter_lines():
            chunk = chunk.strip()
            if chunk:
                data: dict = json.loads(chunk)
                yield Tweet(**data['data'])

    async def get_tweet(self, tweet_id: TweetId):
        data = await self.get(f'/tweets/{tweet_id}', params={
            'tweet.fields': self.DEFAULT_TWEET_FIELDS,
        })
        return Tweet(**data['data'])

    async def delete_tweet(self, tweet_id: TweetId):
        await self.delete(f'/tweets/{tweet_id}')


# TODO: make class derived from pydantic.BaseModel
OAuthToken = dict


class OAuthTokenKind(str, Enum):
    oauth1 = 'oauth1'
    oauth2 = 'oauth2'


@dataclass(frozen=True)
class OAuthManager:
    settings: TwitterOAuth
    scope: str
    name_prefix: str
    suggested_account: str | None = None

    # TODO: move this methods to derived class TwitterOauthManager
    async def obtain_oauth1_token(self) -> OAuthToken:
        async with TwitterApiClient.create_oauth1(oauth=self.settings, redirect_uri='oob') as client:
            await client.client.fetch_request_token('https://api.twitter.com/oauth/request_token')
            auth_url: Url = client.client.create_authorization_url('https://api.twitter.com/oauth/authorize')
            if self.suggested_account is None:
                pin: str = input(f"Open this url {auth_url} and paste here PIN:\n")
            else:
                pin: str = input(f"Switch to {self.suggested_account}, authorize {auth_url} and paste here PIN:\n")
            token: OAuthToken = await client.client.fetch_access_token('https://api.twitter.com/oauth/access_token', verifier=pin)
            await self.save(OAuthTokenKind.oauth1, token)
            return token

    async def obtain_oauth2_token(self) -> OAuthToken:
        client_ctx = TwitterApiClient.create_oauth2(
            scope=self.scope, oauth=self.settings, redirect_uri='http://localhost',
        )
        async with client_ctx as client:
            code_verifier = secrets.token_urlsafe(43)
            url, state = client.client.create_authorization_url(
                url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
            )
            if self.suggested_account is None:
                prompt = f"Follow this url and enter resulting url after redirect: {url}\n"
            else:
                prompt = f"Login to {self.suggested_account}, then authorize and enter resulting url after redirect: {url}\n"
            authorization_response = input(prompt)
            token: OAuthToken = OAuthToken(await client.client.fetch_token(
                authorization_response=authorization_response,
                code_verifier=code_verifier,
            ))
            await self.save(OAuthTokenKind.oauth2, token)
            return token

    async def obtain_token(self, token_kind: OAuthTokenKind) -> OAuthToken:
        match token_kind:
            case OAuthTokenKind.oauth1:
                return await self.obtain_oauth1_token()
            case OAuthTokenKind.oauth2:
                return await self.obtain_oauth2_token()

    def _get_db_key(self, kind: OAuthTokenKind) -> str:
        return f'{self.name_prefix}_{kind.value}'

    async def load(self, kind: OAuthTokenKind) -> OAuthToken:
        async with db.session() as db_session:
            return await OAuthDbLib(db_session).query_oauth_token(self._get_db_key(kind.value))

    async def save(self, kind: OAuthTokenKind, token: OAuthToken):
        async with db.session() as db_session:
            await OAuthDbLib(db_session).save_oauth_token(self._get_db_key(kind.value), token)

    @asynccontextmanager
    async def create_oauth1_client(self):
        token: OAuthToken = await self.load(OAuthTokenKind.oauth1)
        async with TwitterApiClient.create_oauth1(oauth=self.settings, token=token) as client:
            yield client

    async def _update_token(self, token: dict, refresh_token: str):
        logger.debug("Save refreshed oauth2 token for %s", self.name_prefix)
        await self.save(OAuthTokenKind.oauth2, token)

    @asynccontextmanager
    async def create_oauth2_client(self):
        token: OAuthToken = await self.load(OAuthTokenKind.oauth2)
        client_context = TwitterApiClient.create_oauth2(
            scope=self.scope, oauth=self.settings, token=token, update_token=self._update_token,
        )
        async with client_context as client:
            yield client

    @asynccontextmanager
    async def create_apponly_client(self):
        async with TwitterApiClient.create_apponly(token=self.settings.bearer_token) as client:
            yield client


@register_app_command
async def obtain_token(path: str, token_kind: OAuthTokenKind):
    parts = path.split('.')
    module = parts[0]
    obj = importlib.import_module(f'donate4fun.{module}')
    for part in parts[1:]:
        obj = getattr(obj, part)
    await obj.obtain_token(token_kind)


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
