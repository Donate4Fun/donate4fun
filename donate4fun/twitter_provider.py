from datetime import datetime

from furl import furl
from sqlalchemy.orm.exc import NoResultFound

from .db import DbSession
from .db_twitter import TwitterDbLib
from .settings import settings
from .social import SocialProvider
from .models import TwitterAccount, Donation, TwitterTweet
from .types import EntityTooOld
from .twitter import TwitterApiClient
from .twitter_models import UnsupportedTwitterUrl


class TwitterProvider(SocialProvider):
    @staticmethod
    def wrap_db(db_session: DbSession) -> TwitterDbLib:
        return TwitterDbLib(db_session)

    async def query_or_fetch_account(self, db: TwitterDbLib, **params) -> TwitterAccount:
        try:
            account: TwitterAccount = await db.query_account(**params)
            if account.last_fetched_at is None or account.last_fetched_at < datetime.utcnow() - settings.twitter.refresh_timeout:
                raise EntityTooOld
        except (NoResultFound, EntityTooOld):
            async with TwitterApiClient.create_apponly(token=settings.twitter.linking_oauth.bearer_token) as client:
                account: TwitterAccount = await client.get_user_by(**params)
            await db.save_account(account)
        return account

    def get_account_path(self, account: TwitterAccount) -> str:
        return f'/twitter/{account.id}'

    async def apply_target(self, donation: Donation, target: furl, db_session: DbSession):
        parts = target.path.segments
        if len(parts) in (1, 2):
            tweet_id = None
            author_handle = parts[0]
        elif len(parts) >= 3 and parts[1] == 'status':
            tweet_id = int(parts[2])
            author_handle = parts[0]
        else:
            raise UnsupportedTwitterUrl

        db = TwitterDbLib(db_session)
        if tweet_id is not None:
            tweet = TwitterTweet(tweet_id=tweet_id)
            # FIXME: we should possibly save link to the tweet author
            await db.get_or_create_tweet(tweet)
            donation.twitter_tweet = tweet
        self.set_donation_receiver(donation, await self.query_or_fetch_account(db=db, handle=author_handle))
        donation.lightning_address = donation.twitter_account.lightning_address

    def set_donation_receiver(self, donation: Donation, receiver: TwitterAccount):
        donation.twitter_account = receiver

    async def notify(self, donation: Donation):
        if donation.twitter_tweet is not None and donation.twitter_invoice_tweet:
            from .twitter_bot import MentionsBot
            MentionsBot.donation_paid(donation)
