from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import functions

from .db_models import DonatorDb, DonationDb, TransferDb, DonateeDb
from .db_utils import insert_on_conflict_update
from .db import DbSessionWrapper
from .models import BaseModel, Donator, SocialAccount
from .types import InvalidDbState, Satoshi, NotEnoughBalance


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


class SocialDbWrapper(DbSessionWrapper):
    """
    This is base class for classes that provide social provider specific methods
    and it also implements proxy methods for DbSession.
    """
    @classmethod
    @property
    def link_db_model_foreign_key(cls):
        # FIXME: this could be made simpler by unifying link table column names
        return getattr(cls.link_db_model, list(cls.link_db_model.__table__.foreign_keys)[0].parent.name)

    async def query_account(self, *, owner_id: UUID | None = None, **filter_by):
        """
        This is a generic function to get specified by `link_table` social accoutnt for donator (`owner_id`)
        It assumes that first foreign key is linked to a social account table
        """
        foreign_column = first(self.link_db_model.__table__.foreign_keys)
        account_table = foreign_column.column.table
        owner_links = select(self.link_db_model).where(
            (self.link_db_model.donator_id == owner_id) if owner_id is not None else self.link_db_model.via_oauth
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
        return self.owned_model.from_orm(resp.one())

    async def link_account(self, account: BaseModel, donator: Donator, via_oauth: bool) -> bool:
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
        foreign_column = list(self.link_db_model.__table__.foreign_keys)[0]
        result = await self.execute(
            insert(self.link_db_model)
            .values(
                donator_id=donator.id,
                via_oauth=via_oauth,
                **{foreign_column.parent.name: account.id},
            )
            .on_conflict_do_update(
                index_elements=[self.link_db_model.donator_id, foreign_column.parent],
                set_={self.link_db_model.via_oauth: self.link_db_model.via_oauth | via_oauth},
                where=(
                    (self.link_db_model.donator_id == donator.id)
                    & (foreign_column.parent == account.id)
                )
            )
        )
        return result.rowcount == 1

    async def unlink_account(self, account_id: UUID, owner_id: UUID):
        await self.execute(
            delete(self.link_db_model)
            .where(
                (self.link_db_model_foreign_key == account_id)
                & (self.link_db_model.donator_id == owner_id)
            )
        )
        await self.object_changed('donator', owner_id)

    async def transfer_donations(self, account: BaseModel, donator: Donator) -> int:
        """
        Transfers money from social account balance to donator balance
        *social_relation* is a relation inside DonationDb pointing to social account table
        Returns amount transferred
        """
        # FIXME: it should be done simpler
        result = await self.execute(
            select(self.db_model.balance)
            .with_for_update()
            .where(self.db_model.id == account.id)
        )
        amount: int = result.scalar()
        donations_filter = getattr(DonationDb, self.donation_column) == account.id
        transfer_column = first(
            key for key in TransferDb.__table__.foreign_keys if key.column.table is self.db_model.__table__
        ).parent
        await self.start_transfer(
            donator=donator,
            amount=amount,
            donations_filter=donations_filter,
            **{transfer_column.key: account.id},
        )
        await self.execute(
            update(self.db_model)
            .values(balance=self.db_model.balance - amount)
            .where(self.db_model.id == account.id)
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

    async def save_account(self, account: DonateeDb):
        external_key = self.db_model.__table__.info['external_key']
        resp = await self.execute(
            insert_on_conflict_update(self.db_model, account, getattr(self.db_model, external_key))
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(self.db_model.id).where(getattr(self.db_model, external_key) == getattr(account, external_key))
            )
            id_ = resp.scalar()
        account.id = id_

    async def query_accounts(self, *filters) -> list[SocialAccount]:
        result = await self.execute(
            select(self.db_model)
            .where(*filters)
        )
        return [self.model.from_orm(row) for row in result.scalars()]

    async def query_linked_accounts(self, owner_id: UUID) -> list[SocialAccount]:
        result = await self.execute(
            select(*self.db_model.__table__.columns, func.bool_or(self.link_db_model.via_oauth).label('via_oauth'))
            .join(self.link_db_model, self.db_model.id == self.link_db_model_foreign_key)
            .where(self.link_db_model.donator_id == owner_id)
            .group_by(self.db_model.id)
        )
        return [self.owned_model(**obj) for obj in result.all()]

    async def update_balance_for_donation(self, balance_diff: Satoshi, total_diff: Satoshi, donation: DonationDb) -> Satoshi:
        social_account_id: UUID = getattr(donation, self.donation_column)
        resp = await self.execute(
            update(self.db_model)
            .values(
                balance=self.db_model.balance + balance_diff,
                total_donated=self.db_model.total_donated + total_diff,
            )
            .where(self.db_model.id == social_account_id)
            .returning(self.db_model.balance)
        )
        if resp.fetchone().balance < 0:
            raise NotEnoughBalance(f"{self.db_model}[{social_account_id}] hasn't enough money")
        await self.object_changed(f'social:{self.name}', social_account_id)
