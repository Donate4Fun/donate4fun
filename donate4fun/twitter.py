import asyncio
import logging
import time
import secrets
import json
import io
import os
import re
from uuid import UUID
from base64 import b64encode
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote_plus
from typing import Any
from itertools import groupby
from functools import partial

import qrcode
import anyio
import httpx
from qrcode.image.styledpil import StyledPilImage
from lnurl.core import _url_encode as lnurl_encode
from starlette.datastructures import URL
from authlib.integrations.httpx_client import AsyncOAuth1Client, AsyncOAuth2Client
from furl import furl

from .db import DbSession, NoResultFound, Database, db
from .models import Donation, TwitterAccount, TwitterTweet, WithdrawalToken, Donator
from .types import ValidationError, EntityTooOld
from .settings import settings
from .core import as_task, register_command, catch_exceptions
from .api_utils import scrape_lightning_address

logger = logging.getLogger(__name__)


@dataclass
class TwitterDonatee:
    author_handle: str
    tweet_id: str | None = None

    async def fetch(self, donation: Donation, db: DbSession):
        if self.tweet_id is not None:
            tweet = TwitterTweet(tweet_id=self.tweet_id)
            # FIXME: we should possibly save link to the tweet author
            await db.get_or_create_tweet(tweet)
            donation.twitter_tweet = tweet
        donation.twitter_account = await query_or_fetch_twitter_account(db=db, handle=self.author_handle)
        donation.lightning_address = donation.twitter_account.lightning_address


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


def validate_twitter_url(parsed) -> TwitterDonatee:
    parts = parsed.path.split('/')
    if len(parts) in (2, 3):
        return TwitterDonatee(author_handle=parts[1])
    elif len(parts) >= 4 and parts[2] == 'status':
        return TwitterDonatee(tweet_id=int(parts[3]), author_handle=parts[1])
    else:
        raise UnsupportedTwitterUrl


async def query_or_fetch_twitter_account(db: DbSession, **params) -> TwitterAccount:
    try:
        account: TwitterAccount = await db.query_twitter_account(**params)
        if account.last_fetched_at is None or account.last_fetched_at < datetime.utcnow() - settings.twitter.refresh_timeout:
            raise EntityTooOld
    except (NoResultFound, EntityTooOld):
        account: TwitterAccount = await fetch_twitter_author(**params)
        await db.save_twitter_account(account)
    return account


@register_command
async def fetch_and_save_twitter_account(handle: str):
    async with db.session() as db_session:
        account: TwitterAccount = await fetch_twitter_author(handle=handle)
        await db_session.save_twitter_account(account)


async def api_request_raw(method, client, api_path, **kwargs) -> httpx.Response:
    response = await client.request(
        method=method,
        url=urljoin('https://api.twitter.com/2/', api_path),
        **kwargs
    )
    response.raise_for_status()
    return response


async def api_request(method, client, api_path, **kwargs) -> dict[str, Any]:
    response = await api_request_raw(method, client, api_path, **kwargs)
    if response.status_code == 204:
        return
    elif response.headers['content-type'].split(';', 1)[0] == 'application/json':
        data = response.json()
        return data.get('data') or data
    else:
        return response.content


api_get = partial(api_request, 'GET')
api_post = partial(api_request, 'POST')


async def api_get_pages(client, api_path: str, limit: int, params: dict[str, Any], **kwargs):
    results = []
    params_ = params.copy()
    while True:
        response = await api_request_raw('GET', client, api_path, params=params_, **kwargs)
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


async def save_token(db: Database, token: dict[str, Any], refresh_token: str):
    logger.debug(f"new token: {token} ({refresh_token})")
    async with db.session() as db_session:
        await db_session.save_oauth_token('twitter_oauth2', token)


def make_bot_oauth2_client(token=None, update_token=None):
    scope = "tweet.read users.read dm.read dm.write offline.access"
    return make_oauth2_client(scope=scope, token=token, update_token=update_token)


def make_link_oauth2_client(token=None):
    """
    This client is used to link Twitter account to donator (OAuth2 flow)
    """
    return make_oauth2_client(scope='tweet.read users.read', token=token)


@asynccontextmanager
async def make_oauth2_client(scope: str, token=None, update_token=None):
    oauth = settings.twitter.oauth
    async with AsyncOAuth2Client(
        client_id=oauth.client_id,
        client_secret=oauth.client_secret,
        scope=scope,
        token_endpoint='https://api.twitter.com/2/oauth2/token',
        redirect_uri=f'{settings.base_url}/api/v1/twitter/oauth-redirect',
        code_challenge_method='S256',
        token=token,
        update_token=update_token,
    ) as client:
        yield client


@asynccontextmanager
async def make_oauth1_client(**kwargs):
    oauth = settings.twitter.oauth
    async with AsyncOAuth1Client(
        client_id=oauth.consumer_key,
        client_secret=oauth.consumer_secret,
        **kwargs,
    ) as client:
        yield client


@asynccontextmanager
async def make_noauth_client():
    token = settings.twitter.bearer_token
    async with httpx.AsyncClient(headers=dict(authorization=f'Bearer {token}')) as client:
        yield client


@register_command
async def obtain_twitter_oauth2_token():
    async with make_oauth2_client() as client:
        code_verifier = secrets.token_urlsafe(43)
        url, state = client.create_authorization_url(
            url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
        )
        authorization_response = input(f"Follow this url and enter resulting url after redirect: {url}\n")
        token: dict[str, Any] = await client.fetch_token(
            authorization_response=authorization_response,
            code_verifier=code_verifier,
        )
        db = Database(settings.db)
        async with db.session() as db_session:
            await db_session.save_oauth_token('twitter_oauth2', token)


@register_command
async def obtain_twitter_oauth1_token():
    async with make_oauth1_client(redirect_uri='oob') as client:
        await client.fetch_request_token('https://api.twitter.com/oauth/request_token')
        auth_url = client.create_authorization_url('https://api.twitter.com/oauth/authorize')
        pin: str = input(f"Open this url {auth_url} and paste here PIN:\n")
        token: dict[str, Any] = await client.fetch_access_token('https://api.twitter.com/oauth/access_token', verifier=pin)
        db = Database(settings.db)
        async with db.session() as db_session:
            await db_session.save_oauth_token('twitter_oauth1', token)


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


async def fetch_twitter_author(handle: str | None = None, user_id: int | None = None) -> TwitterAccount:
    async with make_noauth_client() as client:
        if handle is not None:
            path = f'users/by/username/{handle}'
        elif user_id is not None:
            path = f'users/{user_id}'
        else:
            raise ValueError("One of handle or user_id should be provided")
        data: dict = await api_get(client, path, params={'user.fields': get_user_fields()})
        return api_data_to_twitter_account(data)


async def fetch_twitter_me(client) -> TwitterAccount:
    data: dict = await api_get(client, 'users/me', params={'user.fields': get_user_fields()})
    return api_data_to_twitter_account(data)


@dataclass
class DirectMessage:
    is_me: bool
    text: str
    created_at: datetime


async def fetch_conversations(client):
    logger.trace("fetching new twitter direct messages")
    params = {
        'dm_event.fields': 'sender_id,created_at,dm_conversation_id',
        'max_results': 100,
    }
    events: list[dict[str, Any]] = await api_get_pages(client, 'dm_events', limit=100, params=params)
    logger.trace("Fetched direct messages %s", events)
    self_id = settings.twitter.self_id

    def keyfunc(event):
        return event['dm_conversation_id']
    for dm_conversation_id, conversation_events in groupby(sorted(events, key=keyfunc), keyfunc):
        sorted_events = sorted(conversation_events, key=lambda event: event['created_at'])
        last_message = sorted_events[-1]
        created_at = datetime.fromisoformat(last_message['created_at'][:-1])  # Remove trailing Z
        if int(last_message['sender_id']) == self_id and created_at < datetime.utcnow() - timedelta(minutes=2):
            # Ignore chats where last message is ours and old
            continue
        yield dm_conversation_id


def get_prove_text_regexp():
    return re.compile(make_prove_message(r'(?P<donator_id>[a-z0-9\-]+)'))


def make_prove_message(donator_id: UUID | str):
    return f'Hereby I confirm that {donator_id} is my Donate4Fun account id'


class Conversation:
    def __init__(self, oauth1_client, oauth2_client, db: Database, conversation_id: str):
        self.oauth1_client = oauth1_client
        self.oauth2_client = oauth2_client
        self.db = db
        self.is_stale = False
        self.conversation_id: str = conversation_id
        self.peer_id = int(conversation_id.replace(str(settings.twitter.self_id), '').replace('-', ''))

    async def fetch_messages(self):
        events = await api_get(
            self.oauth2_client, f'dm_conversations/{self.conversation_id}/dm_events',
            params={'dm_event.fields': 'sender_id,created_at,dm_conversation_id', 'max_results': 100},
        )
        return [DirectMessage(
            text=event['text'],
            created_at=datetime.fromisoformat(event['created_at'][:-1]),  # Remove trailing Z
            is_me=int(event['sender_id']) != self.peer_id,
        ) for event in events]

    async def reply_no_donations(self):
        url = (
            "https://twitter.com/intent/tweet?text="
            + quote_plus("Tip me #Bitcoin through a #LightningNetwork using https://donate4.fun")
        )
        await self.send_text(f"You have no donations, but if you want any then tweet about us {url}")

    async def send_text(self, text: str, **params):
        logger.trace("Sending text to %d: %s", self.peer_id, text)
        await api_post(
            self.oauth2_client, f'dm_conversations/{self.conversation_id}/messages',
            json=dict(text=text, **params),
        )

    async def conversate(self, text: str):
        await self.send_text(text)
        start = time.time()
        while time.time() < start + settings.twitter.answer_timeout:
            await api_get(self.oauth2_client, f'dm_conversations/{self.conversation_id}/dm_events')

    @catch_exceptions
    async def chat_loop(self):
        try:
            while True:
                history = await self.fetch_messages()
                if not history:
                    break
                # Twitter API always returns messages in descending order by created_at
                last_message = history[0]
                logger.trace("last message %s", last_message)
                if last_message.is_me and last_message.created_at < datetime.utcnow() - timedelta(minutes=2):
                    break
                elif not last_message.is_me:
                    logger.info(f"answering to {last_message}")
                    for message in history:
                        if message.is_me:
                            continue
                        if match := get_prove_text_regexp().match(last_message.text):
                            await self.link_twitter_account(match.group('donator_id'))
                            break
                    else:
                        await self.answer_withdraw()
                await asyncio.sleep(5)
        finally:
            self.is_stale = True

    async def link_twitter_account(self, donator_id: str):
        logger.info(f"Linking Twitter account {self.peer_id} to {donator_id}")
        async with self.db.session() as db_session:
            author: TwitterAccount = await query_or_fetch_twitter_account(db_session, user_id=self.peer_id)
            await db_session.link_twitter_account(twitter_author=author, donator=Donator(id=donator_id))
        profile_url = furl(settings.base_url) / 'donator' / donator_id
        await self.send_text(f"Your account is successefully linked. Go to {profile_url} to claim your donations.")

    async def answer_withdraw(self):
        async with self.db.session() as db_session:
            await self.send_text(settings.twitter.greeting)
            try:
                author: TwitterAccount = await db_session.query_twitter_account(user_id=self.peer_id)
            except NoResultFound:
                await self.reply_no_donations()
            else:
                if author.total_donated == 0:
                    await self.reply_no_donations()
                elif author.balance == 0:
                    await self.send_text("All donations have been claimed.")
                elif author.balance < settings.min_withdraw:
                    await self.send_text(
                        f"You have {author.balance} sats, but minimum withdraw amount is {settings.min_withdraw} sats."
                    )
                else:
                    prove_url = f'{settings.base_url}/twitter/prove'
                    await self.send_text(
                        f"You have {author.balance} sats! Go to {prove_url}, connect your Twitter account"
                        " and then you will be able to claim and withdraw your funds."
                    )
                    return
                    # FIXME: this is old code withdraw directly using Twitter. It's not used anymore
                    # because withdrawals are only possible from a Donator account
                    # But if we generate ephemeral Donator account for this and transfer funds there
                    # then user will not be able to withdraw other way, which could be a bad situation
                    # Good solution is to allow users to login to a different donator account when linking social account
                    lnurl: str = await create_withdrawal(db_session, twitter_account=author)
                    qrcode: bytes = make_qr_code(lnurl)
                    media_id: int = await upload_media(self.oauth1_client, qrcode, 'image/png')
                    await self.send_text(
                        "Here are your withdrawal invoice. Scan it with your Bitcoin Lightning Wallet."
                        f" Or copy LNURL: {lnurl}",
                        attachments=[dict(media_id=str(media_id))],
                    )


async def create_withdrawal(db_session, twitter_account):
    # Generate new donator like a new site visitor
    donator = Donator()
    await db_session.link_twitter_account(twitter_author=twitter_account, donator=donator)
    withdrawal_id: UUID = await db_session.create_withdrawal(donator)
    token = WithdrawalToken(withdrawal_id=withdrawal_id)
    url = urljoin(settings.lnd.lnurl_base_url, '/lnurl/withdraw')
    withdraw_url = URL(url).include_query_params(token=token.to_jwt())
    return lnurl_encode(str(withdraw_url))


def make_qr_code(data: str) -> bytes:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    image: StyledPilImage = qr.make_image()
    image_data = io.BytesIO()
    image.save(image_data, "PNG")
    return image_data.getvalue()


@register_command
async def make_withdrawal_lnurl(author_id):
    async with Database(settings.db).session() as db_session:
        lnurl: str = await create_withdrawal(db_session, twitter_author_id=author_id)
        print(f"lightning:{lnurl.lower()}")


@register_command
async def test_make_qr_code(author_id):
    async with Database(settings.db).session() as db_session:
        lnurl: str = await create_withdrawal(db_session, twitter_author_id=author_id)
    qrcode = make_qr_code(lnurl)
    filename = 'tmp-qrcode.png'
    with open(filename, 'wb') as f:
        f.write(qrcode)
    os.system(f'xdg-open {filename}')


async def upload_media(client, image: bytes, mime_type: str) -> int:
    upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
    media_info = await api_post(
        client, upload_url, params=dict(
            command='INIT',
            total_bytes=len(image),
            media_type=mime_type,
            media_category='dm_image',
        )
    )
    media_id = media_info['media_id']
    await api_post(
        client, upload_url,
        data=dict(
            command='APPEND',
            media_id=media_id,
            segment_index=0,
            media_data=b64encode(image).decode(),
        ),
    )
    state_response = await api_post(
        client, upload_url,
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
            state_response = await api_post(
                client, upload_url, params=dict(
                    command='STATUS',
                    media_id=media_id,
                )
            )
    logger.trace("Media uploaded: %s", state_response)
    return media_id


@register_command
async def get_profile_banner():
    async with Database(settings.db).session() as db_session:
        token: dict = await db_session.query_oauth_token('twitter_oauth1')
    async with make_oauth1_client() as client:
        client.token = token
        url = 'https://api.twitter.com/1.1/users/profile_banner.json'
        try:
            response = await api_get(client, url, params=dict(screen_name='elonmusk'))
        except httpx.HTTPStatusError as exc:
            auth_header = exc.request.headers['authorization']
            logger.exception("Failed to get banner image:\n%s\n%s\n%s", auth_header, exc.request.headers, exc.response.json())
        else:
            print(response.json())


@register_command
async def test_upload_media():
    async with Database(settings.db).session() as db_session:
        token: dict = await db_session.query_oauth_token('twitter_oauth1')
    async with make_oauth1_client() as client:
        client.token = token
        try:
            await upload_media(client, open('frontend/public/static/D-16.png', 'rb').read(), 'image/png')
        except httpx.HTTPStatusError as exc:
            auth_header = exc.request.headers['authorization']
            logger.exception("Failed to upload image:\n%s\n%s\n%s", auth_header, exc.request.headers, exc.response.json())


@register_command
async def fetch_twitter_conversations(token: str):
    oauth2_ctx = make_bot_oauth2_client(token=json.loads(token))
    async with oauth2_ctx as oauth2_client:
        print([conversation_id async for conversation_id in fetch_conversations(oauth2_client)])


@as_task
async def run_twitter_bot_restarting(db: Database):
    while True:
        try:
            await run_twitter_bot(db)
        except Exception:
            logger.exception("Exception while running Twitter bot")
            await asyncio.sleep(15)


async def run_twitter_bot(db: Database):
    conversations = {}
    async with db.session() as db_session:
        oauth1_token = await db_session.query_oauth_token('twitter_oauth1')
        oauth2_token = await db_session.query_oauth_token('twitter_oauth2')
        logger.debug("Using tokens %s %s", oauth1_token, oauth2_token)

    oauth1_ctx = make_oauth1_client()
    oauth2_ctx = make_bot_oauth2_client(token=oauth2_token, update_token=partial(save_token, db))
    async with oauth1_ctx as oauth1_client, oauth2_ctx as oauth2_client, anyio.create_task_group() as tg:
        oauth1_client.token = oauth1_token
        while True:
            async for conversation_id in fetch_conversations(oauth2_client):
                if conversation_id not in conversations:
                    logger.debug("Creating conversation %s", conversation_id)
                    conversations[conversation_id] = conversation = Conversation(
                        conversation_id=conversation_id, db=db, oauth2_client=oauth2_client, oauth1_client=oauth1_client,
                    )
                    tg.start_soon(conversation.chat_loop)
            for conversation_id, conversation in conversations.copy().items():
                if conversation.is_stale:
                    logger.debug("Removing conversation %s", conversation_id)
                    del conversations[conversation_id]
            await asyncio.sleep(settings.twitter.dm_check_interval.total_seconds())
