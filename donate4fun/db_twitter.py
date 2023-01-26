from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .models import TwitterAccount, TwitterTweet, TwitterAccountOwned
from .db_models import TwitterAuthorDb, TwitterTweetDb, OAuthTokenDb, TwitterAuthorLink
from .db_social import SocialDbWrapper


class TwitterDbLib(SocialDbWrapper):
    db_model = TwitterAuthorDb
    link_db_model = TwitterAuthorLink
    donation_column = 'twitter_account_id'
    owned_model = TwitterAccountOwned
    model = TwitterAccount
    name = 'twitter'
    donation_field = 'twitter_account'

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

    async def query_oauth_token(self, name: str) -> dict[str, Any]:
        result = await self.execute(
            select(OAuthTokenDb.token)
            .where(OAuthTokenDb.name == name)
        )
        return result.scalars().one()

    async def save_oauth_token(self, name: str, token: dict[str, Any]):
        await self.execute(
            insert(OAuthTokenDb)
            .values(name=name, token=token)
            .on_conflict_do_update(
                index_elements=[OAuthTokenDb.name],
                set_=dict(token=token),
                where=OAuthTokenDb.name == name,
            )
        )
