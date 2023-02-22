import asyncio
import logging
import time
import json
import re
import io
import os
import secrets
from contextlib import asynccontextmanager, AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from itertools import groupby
from typing import AsyncIterator
from urllib.parse import quote_plus, urljoin
from uuid import UUID

import anyio
import httpx
import qrcode
from furl import furl
from qrcode.image.styledpil import StyledPilImage
from lnurl.core import _url_encode as lnurl_encode
from starlette.datastructures import URL

from .db import NoResultFound, db
from .models import TwitterAccount, Donator, WithdrawalToken, Donation, TwitterAccountOwned, TwitterTweet, PaymentRequest
from .core import as_task, catch_exceptions
from .settings import settings
from .twitter import (
    make_oauth2_client, TwitterHandle,
    make_oauth1_client, OAuthTokenLoader, TwitterApiClient, make_apponly_client,
)
from .twitter_provider import TwitterProvider
from .donation import donate
from .api_utils import make_absolute_uri, register_app_command
from .lnd import lnd, LndClient

logger = logging.getLogger(__name__)


@dataclass
class DirectMessage:
    is_me: bool
    text: str
    created_at: datetime


class BaseTwitterBot:
    provider = TwitterProvider()

    @classmethod
    @asynccontextmanager
    async def create(cls) -> AsyncIterator['BaseTwitterBot']:
        async with AsyncExitStack() as stack:
            obj = cls()
            if cls.oauth1_token:
                oauth1_token: dict = await cls.oauth1_token.load()
                oauth1_ctx = make_oauth1_client(oauth=cls.oauth_settings, token=oauth1_token)
                obj.client = TwitterApiClient(await stack.enter_async_context(oauth1_ctx))
            if cls.oauth2_token:
                oauth2_token: dict = await cls.oauth2_token.load()
                oauth2_ctx = make_oauth2_client(scope=cls.oauth2_scope, oauth=cls.oauth_settings, token=oauth2_token)
                obj.oauth2_client = TwitterApiClient(await stack.enter_async_context(oauth2_ctx))
            if cls.oauth_settings.bearer_token:
                apponly_ctx = make_apponly_client(token=cls.oauth_settings.bearer_token)
                obj.apponly_client = TwitterApiClient(await stack.enter_async_context(apponly_ctx))
            yield obj

    @classmethod
    async def obtain_oauth1_token(cls):
        async with make_oauth1_client(oauth=cls.oauth_settings, redirect_uri='oob') as client:
            await client.fetch_request_token('https://api.twitter.com/oauth/request_token')
            auth_url = client.create_authorization_url('https://api.twitter.com/oauth/authorize')
            pin: str = input(f"Open this url {auth_url} and paste here PIN:\n")
            data: dict = await client.fetch_access_token('https://api.twitter.com/oauth/access_token', verifier=pin)
            await cls.oauth1_token.save(data)

    @classmethod
    async def obtain_oauth2_token(cls):
        client_ctx = make_oauth2_client(scope=cls.oauth2_scope, oauth=cls.oauth_settings, redirect_uri='http://localhost')
        async with client_ctx as client:
            code_verifier = secrets.token_urlsafe(43)
            url, state = client.create_authorization_url(
                url='https://twitter.com/i/oauth2/authorize', code_verifier=code_verifier,
            )
            authorization_response = input(f"Follow this url and enter resulting url after redirect: {url}\n")
            token: dict = await client.fetch_token(
                authorization_response=authorization_response,
                code_verifier=code_verifier,
            )
            await cls.oauth2_token.save(token)

    @classmethod
    async def validate_tokens(cls):
        async with cls.create() as bot:
            donate4fun_user_id = 1572908920485576704
            await bot.client.get_user_by(user_id=donate4fun_user_id)
            await bot.oauth2_client.get_user_by(user_id=donate4fun_user_id)
            await bot.apponly_client.get_user_by(user_id=donate4fun_user_id)


def make_prove_message(donator_id: UUID | str):
    return f'Hereby I confirm that {donator_id} is my Donate4Fun account id'


class Conversation:
    def __init__(self, conversation_id: str, api_client: TwitterApiClient):
        self.client: TwitterApiClient = api_client
        self.is_stale: bool = False
        self.conversation_id: str = conversation_id
        self.peer_id: int = int(conversation_id.replace(str(settings.twitter.self_id), '').replace('-', ''))

    async def fetch_messages(self):
        events = await self.client.get(
            f'dm_conversations/{self.conversation_id}/dm_events',
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
        await self.client.post(
            f'/dm_conversations/{self.conversation_id}/messages',
            json=dict(text=text, **params),
        )

    async def conversate(self, text: str):
        await self.send_text(text)
        start = time.time()
        while time.time() < start + settings.twitter.answer_timeout:
            await self.client.get(f'/dm_conversations/{self.conversation_id}/dm_events')

    def get_prove_text_regexp(self):
        return re.compile(make_prove_message(r'(?P<donator_id>[a-z0-9\-]+)'))

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
                        if match := self.get_prove_text_regexp().match(last_message.text):
                            await self.link_twitter_account(match.group('donator_id'))
                            break
                    else:
                        await self.answer_withdraw()
                await asyncio.sleep(5)
        finally:
            self.is_stale = True

    async def link_twitter_account(self, donator_id: str):
        logger.info(f"Linking Twitter account {self.peer_id} to {donator_id}")
        async with db.session() as db_session:
            twitter_db = self.provider.wrap_db(db_session)
            author: TwitterAccount = await self.provider.query_or_fetch_account(twitter_db, user_id=self.peer_id)
            await twitter_db.link_twitter_account(twitter_author=author, donator=Donator(id=donator_id))
        profile_url = furl(settings.base_url) / 'donator' / donator_id
        await self.send_text(f"Your account is successefully linked. Go to {profile_url} to claim your donations.")

    async def answer_withdraw(self):
        async with db.session() as db_session:
            await self.send_text(settings.twitter.conversations_bot.greeting)
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
                    media_id: int = await self.client.upload_media(qrcode, 'image/png', category='dm_image')
                    await self.send_text(
                        "Here are your withdrawal invoice. Scan it with your Bitcoin Lightning Wallet."
                        f" Or copy LNURL: {lnurl}",
                        attachments=[dict(media_id=str(media_id))],
                    )


class ConversationsBot(BaseTwitterBot):
    oauth1_token = OAuthTokenLoader('twitter_converstaions_oauth1')
    oauth2_token = OAuthTokenLoader('twitter_converstaions_oauth2')
    oauth2_scope = "tweet.read users.read dm.read dm.write offline.access"

    @classmethod
    @property
    def oauth_settings(cls):
        return settings.twitter.conversations_bot.oauth

    async def run_loop(self):
        conversations = {}
        async with anyio.create_task_group() as tg:
            while True:
                async for conversation_id in self.fetch_conversations():
                    if conversation_id not in conversations:
                        logger.debug("Creating conversation %s", conversation_id)
                        conversation = Conversation(conversation_id=conversation_id, client=self.client)
                        conversations[conversation_id] = conversation
                        tg.start_soon(conversation.chat_loop)
                for conversation_id, conversation in conversations.copy().items():
                    if conversation.is_stale:
                        logger.debug("Removing conversation %s", conversation_id)
                        del conversations[conversation_id]
                await asyncio.sleep(settings.twitter.dm_check_interval.total_seconds())

    async def fetch_conversations(self):
        logger.trace("fetching new twitter direct messages")
        params = {
            'dm_event.fields': 'sender_id,created_at,dm_conversation_id',
            'max_results': 100,
        }
        events: list[dict] = await self.oauth2_client.get_pages('dm_events', limit=100, params=params)
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


register_app_command(ConversationsBot.obtain_oauth1_token, 'obtain_conversations_bot_oauth1_token')
register_app_command(ConversationsBot.obtain_oauth2_token, 'obtain_conversations_bot_oauth2_token')


class MentionsBot(BaseTwitterBot):
    oauth1_token = OAuthTokenLoader('twitter_mentions_bot_oauth1')
    oauth2_token = OAuthTokenLoader('twitter_mentions_bot_oauth2')
    oauth2_scope = "tweet.read tweet.write users.read dm.read dm.write offline.access"

    @classmethod
    @property
    def oauth_settings(cls):
        return settings.twitter.mentions_bot.oauth

    async def run_loop(self, handle: TwitterHandle):
        try:
            async with anyio.create_task_group() as tg:
                async for mention in self.fetch_mentions(handle):
                    tg.start_soon(self.handle_mention, mention)
        except httpx.HTTPStatusError as exc:
            print(exc.response.json())
            raise

    async def handle_mention(self, mention: dict):
        logger.trace("handling mention %s", mention)
        receiver_user_id: int = int(mention['in_reply_to_user_id'])
        donator_user_id: int = int(mention['author_id'])
        referenced_tweet_id: int = int(mention['referenced_tweets'][0]['id'])
        tweet_id: int = int(mention['id'])
        text: str = mention['text']
        async with db.session() as db_session:
            twitter_db = self.provider.wrap_db(db_session)
            donator_account_: TwitterAccount = await self.provider.query_or_fetch_account(db=twitter_db, user_id=donator_user_id)
            donator_account: TwitterAccountOwned = await twitter_db.query_account(id=donator_account_.id)
            if donator_account.owner_id is None:
                donator = Donator()
            else:
                donator = Donator(id=donator_account.owner_id)
            receiver_account: TwitterAccount = await self.provider.query_or_fetch_account(db=twitter_db, user_id=receiver_user_id)
            if match := re.search(r' (?P<amount>\d+) ?(?P<has_k>[kK])?', text):
                amount = int(match['amount'])
                if match['has_k']:
                    amount *= 1000
            else:
                await self.do_not_understand(tweet_id)
                return
            logger.debug(
                "handling donation from @%s to @%s for %d sats via tweet %d",
                donator_account.handle, receiver_account.handle, amount, tweet_id,
            )
            tweet: TwitterTweet = TwitterTweet(tweet_id=referenced_tweet_id)
            await twitter_db.get_or_create_tweet(tweet)
            donation = Donation(
                donator=donator,
                twitter_account=receiver_account,
                twitter_tweet=tweet,
                donator_twitter_account=donator_account,
                amount=amount,
            )
            with lnd.assign(LndClient(settings.lnd)):
                # Long expiry because this will be posted in Twitter
                pay_req, donation = await donate(donation, db_session, expiry=3600)
            if pay_req:
                await self.send_payreq(tweet_id, receiver_account.handle, pay_req)
            elif donation.paid_at:
                await self.share_donation_preview(tweet_id, donation)
            else:
                raise RuntimeError("invalid state")

    async def invite_new_user(self, tweet_id: int):
        print("inviting new user")

    async def do_not_understand(self, tweet_id: int):
        print("i do not understand")

    async def share_donation_preview(self, tweet_id: int, donation: Donation):
        await self.send_tweet(reply_to=tweet_id, text=make_absolute_uri(f'/donation/{donation.id}'))

    async def send_payreq(self, tweet_id: int, handle: TwitterHandle, pay_req: PaymentRequest):
        qrcode: bytes = make_qr_code(pay_req)
        media_id: int = await self.client.upload_media(qrcode, 'image/png', category='tweet_image')
        url: str = make_absolute_uri(f'/lnurlp/twitter/{handle}')
        await self.send_tweet(text=f"Invoice: {url}", reply_to=tweet_id, media_id=media_id)

    async def fetch_mentions(self, handle: TwitterHandle) -> AsyncIterator[dict]:
        logger.info("fetching new mentions for @%s", handle)
        current_rules: list = (await self.apponly_client.get('/tweets/search/stream/rules')).get('data', [])
        logger.debug("current rules: %s", current_rules)
        expected_rules = [dict(value=f'@{handle} is:reply -from:{handle}')]
        if [dict(value=rule['value']) for rule in current_rules] != expected_rules:
            logger.debug("current rules differ with expected, overriding with %s", expected_rules)
            if current_rules:
                current_rule_ids = [rule['id'] for rule in current_rules]
                await self.apponly_client.post('/tweets/search/stream/rules', json=dict(
                    delete=dict(ids=current_rule_ids)
                ))
            await self.apponly_client.post('/tweets/search/stream/rules', json=dict(
                add=expected_rules,
            ))
        params = {
            'tweet.fields': 'created_at',
            'expansions': 'author_id,referenced_tweets.id,in_reply_to_user_id,referenced_tweets.id.author_id',
        }
        async with self.apponly_client.stream('GET', '/tweets/search/stream', params=params, timeout=3600) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                chunk = chunk.strip()
                if chunk:
                    data: dict = json.loads(chunk)
                    yield data['data']

    async def send_tweet(self, reply_to: int = None, text: str = None, media_id: int = None):
        body = {}
        if reply_to is not None:
            body['reply'] = dict(in_reply_to_tweet_id=str(reply_to))
        if text is not None:
            body['text'] = text
        if media_id is not None:
            body['media'] = dict(media_ids=[str(media_id)])
        tweet = (await self.client.post('/tweets', json=body))['data']
        logger.trace("tweeted https://twitter.com/status/%s: %s", tweet['id'], tweet['text'])


register_app_command(MentionsBot.obtain_oauth1_token, 'obtain_mentions_bot_oauth1_token')
register_app_command(MentionsBot.obtain_oauth2_token, 'obtain_mentions_bot_oauth2_token')
register_app_command(MentionsBot.validate_tokens, 'validate_mentions_bot_tokens')


@register_app_command
async def test_upload_media():
    async with make_oauth1_client(token=await MentionsBot.oauth1_token.load()) as client:
        try:
            with open('frontend/public/static/D-16.png', 'rb') as f:
                await client.upload_media(f.read(), 'image/png', category='tweet_image')
        except httpx.HTTPStatusError as exc:
            auth_header = exc.request.headers['authorization']
            logger.exception("Failed to upload image:\n%s\n%s\n%s", auth_header, exc.request.headers, exc.response.json())


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


@register_app_command
async def make_withdrawal_lnurl(author_id):
    async with db.session() as db_session:
        lnurl: str = await create_withdrawal(db_session, twitter_author_id=author_id)
        print(f"lightning:{lnurl.lower()}")


@register_app_command
async def test_make_qr_code(author_id):
    async with db.session() as db_session:
        lnurl: str = await create_withdrawal(db_session, twitter_author_id=author_id)
    qrcode = make_qr_code(lnurl)
    filename = 'tmp-qrcode.png'
    with open(filename, 'wb') as f:
        f.write(qrcode)
    os.system(f'xdg-open {filename}')


@register_app_command
async def fetch_twitter_conversations(token: str):
    async with ConversationsBot.create() as bot:
        print([conversation_id async for conversation_id in bot.fetch_conversations()])


def restarting(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                await func(*args, **kwargs)
            except Exception:
                delay = 15
                logger.exception("Exception in %s, restarting in %d seconds", func, delay)
                await asyncio.sleep(delay)
    return wrapper


@as_task
@register_app_command
@restarting
async def run_conversations_bot():
    async with ConversationsBot.create() as bot:
        await bot.run_loop()


@as_task
@register_app_command
@restarting
async def run_mentions_bot():
    async with MentionsBot.create() as bot:
        me: TwitterAccount = await bot.client.get_me()
        await bot.run_loop(me.handle)
