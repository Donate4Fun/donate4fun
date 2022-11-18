from uuid import UUID
from typing import Any
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import TwitterAccount, TwitterTweet, Donator, TwitterAccountOwned
from .db_models import TwitterAuthorDb, TwitterTweetDb, OAuthTokenDb, TwitterAuthorLink, DonatorDb, TransferDb


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

    async def save_twitter_account(self, author: TwitterAccount):
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

    async def query_donator_twitter_accounts(self, donator_id: UUID) -> list[TwitterAccount]:
        result = await self.execute(
            select(TwitterAuthorDb)
            .join(TwitterAuthorLink, TwitterAuthorDb.id == TwitterAuthorLink.twitter_author_id)
            .where(TwitterAuthorLink.donator_id == donator_id)
        )
        return [TwitterAccount.from_orm(obj) for obj in result.unique().scalars()]

    async def link_twitter_account(self, twitter_author: TwitterAccount, donator: Donator):
        await self.execute(
            insert(TwitterAuthorLink)
            .values(
                twitter_author_id=twitter_author.id,
                donator_id=donator.id,
            )
            .on_conflict_do_nothing()
        )

    async def query_twitter_account(self, owner_id: UUID | None = None, **filter_by) -> TwitterAccountOwned:
        owner_links = select(TwitterAuthorLink).where(TwitterAuthorLink.donator_id == owner_id).subquery()
        accounts = select(TwitterAuthorDb).filter_by(**filter_by).subquery()
        resp = await self.execute(
            select(accounts, owner_links.c.donator_id.is_not(None).label('is_my'))
            .join(
                owner_links,
                onclause=accounts.c.id == owner_links.c.twitter_author_id,
                isouter=True,
            )
        )
        return TwitterAccountOwned.from_orm(resp.one())

    async def transfer_twitter_donations(self, twitter_account: TwitterAccount, donator: Donator) -> int:
        """
        Transfers money from Twitter account balance to donator balance
        Returns amount transferred
        """
        result = await self.execute(
            select(TwitterAuthorDb.balance)
            .with_for_update()
            .where(TwitterAuthorDb.id == twitter_account.id)
        )
        amount: int = result.scalar()
        await self.execute(
            insert(TransferDb)
            .values(
                amount=amount,
                donator_id=donator.id,
                twitter_author_id=twitter_account.id,
                created_at=datetime.utcnow(),
            )
        )
        await self.execute(
            update(TwitterAuthorDb)
            .values(balance=TwitterAuthorDb.balance - amount)
            .where(TwitterAuthorDb.id == twitter_account.id)
        )
        await self.execute(
            update(DonatorDb)
            .values(balance=DonatorDb.balance + amount)
            .where(DonatorDb.id == donator.id)
        )
        await self.object_changed('donator', donator.id)
        return amount


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
