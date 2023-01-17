from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from .models import TwitterAccount, TwitterTweet, Donator, TwitterAccountOwned
from .db_models import TwitterAuthorDb, TwitterTweetDb, OAuthTokenDb, TwitterAuthorLink, DonationDb
from .db_utils import insert_on_conflict_update
from .db_social import SocialDbMixin


class TwitterDbMixin(SocialDbMixin):
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

    async def save_twitter_account(self, author: TwitterAccount):
        resp = await self.execute(
            insert_on_conflict_update(TwitterAuthorDb, author, TwitterAuthorDb.user_id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(TwitterAuthorDb.id).where(TwitterAuthorDb.user_id == author.user_id)
            )
            id_ = resp.scalar()
        author.id = id_

    async def query_donator_twitter_accounts(self, donator_id: UUID) -> list[TwitterAccountOwned]:
        result = await self.execute(
            select(*TwitterAuthorDb.__table__.columns, func.bool_or(TwitterAuthorLink.via_oauth).label('via_oauth'))
            .join(TwitterAuthorLink, TwitterAuthorDb.id == TwitterAuthorLink.twitter_author_id)
            .where(TwitterAuthorLink.donator_id == donator_id)
            .group_by(TwitterAuthorDb.id)
        )
        return [TwitterAccountOwned(**obj) for obj in result.all()]

    async def link_twitter_account(self, twitter_author: TwitterAccount, donator: Donator, via_oauth: bool):
        """
        Links Twitter author to the donator account.
        Returns True if new link is created, False otherwise
        """
        return await self.link_social_account(TwitterAuthorLink, twitter_author, donator, via_oauth)

    async def unlink_twitter_account(self, account_id: UUID, owner_id: UUID):
        await self.unlink_social_account(TwitterAuthorLink, account_id, owner_id)

    async def query_twitter_account(self, owner_id: UUID | None = None, **filter_by) -> TwitterAccountOwned:
        return TwitterAccountOwned.from_orm(
            await self.query_social_account(TwitterAuthorLink, owner_id=owner_id, **filter_by)
        )

    async def transfer_twitter_donations(self, twitter_account: TwitterAccount, donator: Donator) -> int:
        """
        Transfers money from Twitter account balance to donator balance
        Returns amount transferred
        """
        return await self.transfer_social_donations(DonationDb.twitter_account, twitter_account, donator)

    async def query_twitter_accounts(self, *filters) -> list[TwitterAccount]:
        result = await self.execute(
            select(TwitterAuthorDb)
            .where(*filters)
        )
        return [TwitterAccount.from_orm(row) for row in result.scalars()]


class OAuthTokenDbMixin:
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
