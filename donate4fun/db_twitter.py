from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .models import TwitterAccount, TwitterTweet, TwitterAccountOwned, Donation
from .db_models import TwitterAuthorDb, TwitterTweetDb, TwitterAuthorLink, DonationDb
from .db_social import SocialDbWrapper
from .twitter_models import Tweet


class TwitterDbLib(SocialDbWrapper):
    db_model = TwitterAuthorDb
    link_db_model = TwitterAuthorLink
    donation_column = 'twitter_account_id'
    owned_model = TwitterAccountOwned
    model = TwitterAccount
    name = 'twitter'
    donation_field = 'twitter_account'
    db_model_name_column = 'name'
    db_model_thumbnail_url_column = 'profile_image_url'

    async def get_or_create_tweet(self, tweet: TwitterTweet) -> TwitterAuthorDb:
        resp = await self.execute(
            insert(TwitterTweetDb)
            .values(tweet.dict())
            .on_conflict_do_nothing()
            .returning(TwitterTweetDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(TwitterTweetDb.id).where(TwitterTweetDb.tweet_id == tweet.tweet_id)
            )
            id_ = resp.scalar()
        tweet.id = id_

    async def add_invoice_tweet_to_donation(self, donation: Donation, tweet: Tweet):
        await self.execute(
            update(DonationDb)
            .values(twitter_invoice_tweet_id=tweet.id)
            .where(DonationDb.id == donation.id)
        )
