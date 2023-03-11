import asyncio
import logging
import time
import re
import io
import os
from abc import abstractmethod
from collections import defaultdict
from contextlib import asynccontextmanager, AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps, cache
from typing import AsyncIterator
from urllib.parse import quote_plus, urljoin
from uuid import UUID

import anyio
import httpx
import qrcode
from furl import furl
from qrcode.image.styledpil import StyledPilImage
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M
from lnurl.core import _url_encode as lnurl_encode
from starlette.datastructures import URL

from .db import NoResultFound, db
from .db_donations import DonationsDbLib
from .models import (
    TwitterAccount, Donator, WithdrawalToken, Donation, TwitterAccountOwned, TwitterTweet, PaymentRequest, Notification,
)
from .core import as_task, catch_exceptions
from .settings import settings
from .twitter import TwitterHandle, OAuthManager, TwitterApiClient, Tweet
from .twitter_provider import TwitterProvider
from .donation import donate
from .api_utils import make_absolute_uri, register_app_command
from .lnd import lnd, LndClient
from .pubsub import pubsub

logger = logging.getLogger(__name__)


@dataclass
class DirectMessage:
    is_me: bool
    text: str
    created_at: datetime


class BaseTwitterBot:
    provider = TwitterProvider()

    @property
    @abstractmethod
    def oauth_manager(self):
        ...

    @classmethod
    @asynccontextmanager
    async def create(cls) -> AsyncIterator['BaseTwitterBot']:
        async with AsyncExitStack() as stack:
            self_ = cls()
            self_.oauth1_client = await stack.enter_async_context(self_.oauth_manager.create_oauth1_client())
            self_.oauth2_client = await stack.enter_async_context(self_.oauth_manager.create_oauth2_client())
            self_.apponly_client = await stack.enter_async_context(self_.oauth_manager.create_apponly_client())
            yield self_

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
    @classmethod
    @property
    @cache
    def oauth_manager(cls):
        return OAuthManager(
            name_prefix='twitter_converstaions',
            settings=settings.twitter.conversations_bot.oauth,
            scope="tweet.read users.read dm.read dm.write offline.access",
        )

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
        conversations = defaultdict(list)
        async for event in self.oauth2_client.get_pages('dm_events', params=params):
            conversations[event['dm_conversation_id']].append(event)
        logger.trace("Fetched direct messages: %s", conversations)
        self_id = settings.twitter.self_id

        for dm_conversation_id, conversation_events in conversations:
            sorted_events = sorted(conversation_events, key=lambda event: event['created_at'])
            last_message = sorted_events[-1]
            created_at = datetime.fromisoformat(last_message['created_at'][:-1])  # Remove trailing Z
            if int(last_message['sender_id']) == self_id and created_at < datetime.utcnow() - timedelta(minutes=2):
                # Ignore chats where last message is ours and old
                continue
            yield dm_conversation_id


class MentionsBot(BaseTwitterBot):
    @classmethod
    @property
    @cache
    def oauth_manager(self):
        return OAuthManager(
            name_prefix='twitter_mentions_bot',
            scope="tweet.read tweet.write users.read dm.read dm.write offline.access",
            settings=settings.twitter.mentions_bot.oauth,
            suggested_account='tip4fun',
        )

    @classmethod
    @asynccontextmanager
    async def create(cls):
        async with super().create() as self_:
            me: TwitterAccount = await self_.oauth2_client.get_me()
            self_.handle = me.handle
            yield self_

    async def run_loop(self):
        try:
            async with anyio.create_task_group() as tg:
                async with self.fetch_mentions() as mentions:
                    async for mention in mentions:
                        tg.start_soon(self.handle_mention, mention)
        except httpx.HTTPStatusError as exc:
            print(exc.response.json())
            raise

    async def handle_mention(self, mention: Tweet) -> Donation:
        logger.trace("handling mention %s", mention)
        async with db.session() as db_session:
            twitter_db = self.provider.wrap_db(db_session)
            donator_account_: TwitterAccount = await self.provider.query_or_fetch_account(
                db=twitter_db, user_id=mention.author_id,
            )
            donator_account: TwitterAccountOwned = await twitter_db.query_account(id=donator_account_.id)
            if donator_account.owner_id is None:
                donator = Donator()
            else:
                donator = Donator(id=donator_account.owner_id)
            receiver_account: TwitterAccount = await self.provider.query_or_fetch_account(
                db=twitter_db, user_id=mention.in_reply_to_user_id,
            )
            if match := re.search(r' (?P<amount>\d+) ?(?P<has_k>[kK])?', mention.text):
                amount = int(match['amount'])
                if match['has_k']:
                    amount *= 1000
            else:
                await self.do_not_understand(mention.id)
                return
            logger.debug(
                "handling donation from @%s to @%s for %d sats via tweet %d",
                donator_account.handle, receiver_account.handle, amount, mention.id,
            )
            tweet: TwitterTweet = TwitterTweet(tweet_id=mention.referenced_tweets[0].id)
            await twitter_db.get_or_create_tweet(tweet)
            donation = Donation(
                donator=donator,
                twitter_account=receiver_account,
                twitter_tweet=tweet,
                donator_twitter_account=donator_account,
                amount=amount,
                lightning_address=receiver_account.lightning_address,
            )
            with lnd.assign(LndClient(settings.lnd)):
                # Long expiry because this will be posted on Twitter
                pay_req, donation = await donate(donation, db_session, expiry=3600 * 24)
        if pay_req:
            invoice_tweet = await self.send_payreq(mention.id, receiver_account.handle, donation, pay_req)
            async with db.session() as db_session:
                twitter_db = self.provider.wrap_db(db_session)
                await twitter_db.add_invoice_tweet_to_donation(donation=donation, tweet=invoice_tweet)
        elif donation.paid_at:
            await self.share_donation_preview(mention.id, donation)
        else:
            raise RuntimeError("invalid state")
        return donation

    async def invite_new_user(self, tweet_id: int):
        print("inviting new user")

    async def do_not_understand(self, tweet_id: int):
        print("i do not understand")

    async def share_donation_preview(self, tweet_id: int, donation: Donation):
        await self.oauth2_client.send_tweet(reply_to=tweet_id, text=make_absolute_uri(f'/donation/{donation.id}'))

    async def send_payreq(self, tweet_id: int, handle: TwitterHandle, donation: Donation, pay_req: PaymentRequest) -> Tweet:
        qrcode: bytes = make_qr_code(pay_req, ERROR_CORRECT_M)
        media_id: int = await self.oauth1_client.upload_media(qrcode, 'image/png', category='tweet_image')
        invoice_url = make_absolute_uri(f'/api/v1/donation/{donation.id}/invoice')
        return await self.oauth2_client.send_tweet(text=f"Invoice: {invoice_url}", reply_to=tweet_id, media_id=media_id)

    def fetch_mentions(self) -> AsyncIterator[AsyncIterator[Tweet]]:
        logger.info("fetching new mentions for @%s", self.handle)
        return self.apponly_client.stream_tweets(query=f'@{self.handle} is:reply -from:{self.handle}')

    @asynccontextmanager
    async def monitor_invoices(self) -> AsyncIterator[AsyncIterator[Donation]]:
        queue = asyncio.Queue()
        async with pubsub.subscribe('donations', queue.put):
            yield self.process_invoices(queue)

    async def process_invoices(self, queue: asyncio.Queue) -> AsyncIterator[Donation]:
        while True:
            data: str = await queue.get()
            notification = Notification.from_json(data)
            async with db.session() as db_session:
                donation: Donation = await DonationsDbLib(db_session).query_donation(id=notification.id)
                logger.trace("received notifiaction about %s", donation)
                if donation.twitter_invoice_tweet_id is not None:
                    # TODO: use task group
                    invoice_tweet: Tweet = await self.oauth2_client.get_tweet(donation.twitter_invoice_tweet_id)
                    await self.oauth2_client.delete_tweet(donation.twitter_invoice_tweet_id)
                    await self.share_donation_preview(tweet_id=invoice_tweet.replied_to, donation=donation)
                    yield donation


@register_app_command
async def test_upload_media():
    async with TwitterApiClient.create_oauth1(token=await MentionsBot.oauth1_token.load()) as client:
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


def make_qr_code(data: str, error_correction: int = ERROR_CORRECT_H) -> bytes:
    """
    L - 7%
    M - 15%
    Q - 25%
    H - 30%
    """
    qr = qrcode.QRCode(error_correction=error_correction)
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
        await bot.run_loop()
