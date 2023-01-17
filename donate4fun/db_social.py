from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import functions

from .db_models import Base, DonatorDb, DonationDb, TransferDb
from .models import BaseModel, Donator
from .types import InvalidDbState


def claimable_donation_filter():
    return (
        DonationDb.claimed_at.is_(None)
        & DonationDb.paid_at.is_not(None)
        & DonationDb.cancelled_at.is_(None)
    )


def first(iterable):
    try:
        return next(iter(iterable))
    except StopIteration as exc:
        raise IndexError from exc


class SocialDbMixin:
    async def query_social_account(self, link_table: Base, *, owner_id: UUID | None = None, **filter_by):
        """
        This is a generic function to get specified by `link_table` social accoutnt for donator (`owner_id`)
        It assumes that first foreign key is linked to a social account table
        """
        foreign_column = first(link_table.__table__.foreign_keys)
        account_table = foreign_column.column.table
        owner_links = select(link_table).where(
            (link_table.donator_id == owner_id) if owner_id is not None else link_table.via_oauth
        ).subquery()
        resp = await self.execute(
            select(
                *account_table.c,
                owner_links.c.donator_id.label('owner_id'),
                func.coalesce(owner_links.c.via_oauth, False).label('via_oauth'),
            )
            .filter_by(**filter_by)
            .outerjoin(
                owner_links,
                onclause=account_table.c.id == owner_links.c[foreign_column.parent.name],
            )
        )
        return resp.one()

    async def link_social_account(self, link_table: Base, account: BaseModel, donator: Donator, via_oauth: bool) -> bool:
        """
        Links a social account to the donator account.
        Returns True if new link is created, False otherwise
        """
        # Ensure that donator is saved in DB
        # Do no use save_donator because it overwrites fields like lnauth_pubkey which could be uninitialized in `donator`
        await self.execute(
            insert(DonatorDb)
            .values(**donator.dict(exclude={'connected'}))
            .on_conflict_do_nothing()
        )
        foreign_column = list(link_table.__table__.foreign_keys)[0]
        result = await self.execute(
            insert(link_table)
            .values(
                donator_id=donator.id,
                via_oauth=via_oauth,
                **{foreign_column.parent.name: account.id},
            )
            .on_conflict_do_update(
                index_elements=[link_table.donator_id, foreign_column.parent],
                set_={link_table.via_oauth: link_table.via_oauth | via_oauth},
                where=(
                    (link_table.donator_id == donator.id)
                    & (foreign_column.parent == account.id)
                )
            )
        )
        return result.rowcount == 1

    async def unlink_social_account(self, link_table: Base, account_id: UUID, owner_id: UUID):
        foreign_column = getattr(link_table, list(link_table.__table__.foreign_keys)[0].parent.name)
        await self.execute(
            delete(link_table)
            .where(
                (foreign_column == account_id)
                & (link_table.donator_id == owner_id)
            )
        )
        await self.object_changed('donator', owner_id)

    async def transfer_social_donations(self, social_relation, account: BaseModel, donator: Donator) -> int:
        """
        Transfers money from social account balance to donator balance
        *social_relation* is a relation inside DonationDb pointing to social account table
        Returns amount transferred
        """
        # FIXME: it should be done simpler
        foreign_column = first(social_relation.prop.local_columns)
        social_table = social_relation.prop.mapper.class_
        result = await self.execute(
            select(social_table.balance)
            .with_for_update()
            .where(social_table.id == account.id)
        )
        amount: int = result.scalar()
        donations_filter = getattr(DonationDb, foreign_column.key) == account.id
        transfer_column = first(
            key for key in TransferDb.__table__.foreign_keys if key.column.table is social_table.__table__
        ).parent
        await self.start_transfer(
            donator=donator,
            amount=amount,
            donations_filter=donations_filter,
            **{transfer_column.key: account.id},
        )
        await self.execute(
            update(social_table)
            .values(balance=social_table.balance - amount)
            .where(social_table.id == account.id)
        )
        await self.finish_transfer(amount=amount, donator=donator, donations_filter=donations_filter)
        return amount

    async def start_transfer(self, donator: Donator, amount: int, donations_filter, **transfer_fields):
        """
        Ensures that Donator's balance and sum of unclaimed donations match.
        Then it creates a corresponding Transfer using *transfer_fields*.
        """
        subquery = (
            select(DonationDb)
            .where(claimable_donation_filter() & donations_filter)
            .with_for_update()
            .subquery()
        )
        result = await self.execute(
            select(func.coalesce(func.sum(subquery.c.amount), 0).label('amount'))
        )
        sum_amount: int = result.fetchone().amount
        if sum_amount != amount:
            raise InvalidDbState(f"Sum of donations ({sum_amount}) != account balance ({amount})")
        await self.execute(
            insert(TransferDb)
            .values(
                amount=amount,
                donator_id=donator.id,
                created_at=functions.now(),
                **transfer_fields,
            )
        )

    async def finish_transfer(self, donator: Donator, amount: int, donations_filter):
        await self.execute(
            update(DonationDb)
            .values(claimed_at=functions.now())
            .where(claimable_donation_filter() & donations_filter)
        )
        await self.execute(
            update(DonatorDb)
            .values(balance=DonatorDb.balance + amount)
            .where(DonatorDb.id == donator.id)
        )
        await self.object_changed('donator', donator.id)
