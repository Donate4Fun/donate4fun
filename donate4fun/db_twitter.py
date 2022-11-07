from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import TwitterAuthor, TwitterTweet
from .db_models import TwitterAuthorDb, TwitterTweetDb


class TwitterDbMixin:
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

    async def save_twitter_author(self, author: TwitterAuthor):
        resp = await self.execute(
            insert(TwitterAuthorDb)
            .values(author.dict())
            .on_conflict_do_update(
                index_elements=[TwitterAuthorDb.user_id],
                set_={
                    TwitterAuthorDb.name: author.name,
                    TwitterAuthorDb.profile_image_url: author.profile_image_url,
                },
                where=(
                    (func.coalesce(TwitterAuthorDb.name, '') != author.name)
                    | (func.coalesce(TwitterAuthorDb.handle, '') != author.handle)
                    | (func.coalesce(TwitterAuthorDb.profile_image_url, '') != author.profile_image_url)
                ),
            )
            .returning(TwitterAuthorDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(TwitterAuthorDb.id).where(TwitterAuthorDb.user_id == author.user_id)
            )
            id_ = resp.scalar()
        author.id = id_

    async def query_twitter_author(self, handle: str) -> TwitterAuthor:
        resp = await self.execute(
            select(TwitterAuthorDb)
            .where(TwitterAuthorDb.handle == handle)
        )
        return TwitterAuthor.from_orm(**resp.scalars().one())
