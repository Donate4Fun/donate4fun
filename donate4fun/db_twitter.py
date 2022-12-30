from typing import Any
from uuid import UUID

from sqlalchemy import select, update, func, delete
from sqlalchemy.dialects.postgresql import insert

from .models import TwitterAccount, TwitterTweet, Donator, TwitterAccountOwned
from .db_models import TwitterAuthorDb, TwitterTweetDb, OAuthTokenDb, TwitterAuthorLink, DonationDb, DonatorDb
from .db_utils import insert_on_conflict_update


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
        # Do no use save_donator because it overwrites fields like lnauth_pubkey which could be uninitialized in `donator`
        await self.execute(
            insert(DonatorDb)
            .values(**donator.dict(exclude={'connected'}))
            .on_conflict_do_nothing()
        )
        result = await self.execute(
            insert(TwitterAuthorLink)
            .values(
                twitter_author_id=twitter_author.id,
                donator_id=donator.id,
                via_oauth=via_oauth,
            )
            .on_conflict_do_update(
                index_elements=[TwitterAuthorLink.donator_id, TwitterAuthorLink.twitter_author_id],
                set_={TwitterAuthorLink.via_oauth: TwitterAuthorLink.via_oauth | via_oauth},
                where=(
                    (TwitterAuthorLink.donator_id == donator.id)
                    & (TwitterAuthorLink.twitter_author_id == twitter_author.id)
                )
            )
        )
        return result.rowcount == 1

    async def query_twitter_account(self, owner_id: UUID | None = None, **filter_by) -> TwitterAccountOwned:
        owner_links = select(TwitterAuthorLink).where(
            (TwitterAuthorLink.donator_id == owner_id) if owner_id is not None else TwitterAuthorLink.via_oauth
        ).subquery()
        resp = await self.execute(
            select(
                *TwitterAuthorDb.__table__.c,
                owner_links.c.donator_id.label('owner_id'),
                owner_links.c.via_oauth,
            )
            .filter_by(**filter_by)
            .outerjoin(
                owner_links,
                onclause=TwitterAuthorDb.id == owner_links.c.twitter_author_id,
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
        donations_filter = DonationDb.twitter_account_id == twitter_account.id
        await self.start_transfer(
            donator=donator,
            amount=amount,
            donations_filter=donations_filter,
            twitter_author_id=twitter_account.id,
        )
        await self.execute(
            update(TwitterAuthorDb)
            .values(balance=TwitterAuthorDb.balance - amount)
            .where(TwitterAuthorDb.id == twitter_account.id)
        )
        await self.finish_transfer(amount=amount, donator=donator, donations_filter=donations_filter)
        return amount

    async def query_twitter_accounts(self, *filters) -> list[TwitterAccount]:
        result = await self.execute(
            select(TwitterAuthorDb)
            .where(*filters)
        )
        return [TwitterAccount.from_orm(row) for row in result.scalars()]

    async def unlink_twitter_account(self, account_id: UUID, owner_id: UUID):
        await self.execute(
            delete(TwitterAuthorLink)
            .where(
                (TwitterAuthorLink.twitter_author_id == account_id)
                & (TwitterAuthorLink.donator_id == owner_id)
            )
        )
        await self.object_changed('donator', owner_id)


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
