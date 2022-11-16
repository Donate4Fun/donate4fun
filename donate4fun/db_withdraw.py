from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .types import NotFound
from .db_models import WithdrawalDb, DonatorDb
from .models import Notification


class WithdrawalDbMixin:
    async def create_withdrawal(self, donator: DonatorDb) -> UUID:
        result = await self.execute(
            insert(WithdrawalDb)
            .values(
                created_at=datetime.utcnow(),
                donator_id=donator.id,
                amount=donator.balance,
            )
            .returning(WithdrawalDb.id)
        )
        return result.scalars().one()

    async def query_withdrawal(self, withdrawal_id: UUID) -> WithdrawalDb:
        result = await self.execute(
            select(WithdrawalDb)
            .where(WithdrawalDb.id == withdrawal_id)
        )
        return result.scalars().one()

    async def withdraw(self, withdrawal_id: UUID, amount: int) -> int:
        """
        Save withdrawal changes to db - this happens after the payment
        Returns new balance
        """
        result = await self.execute(
            update(WithdrawalDb)
            .values(
                paid_at=datetime.utcnow(),
                amount=amount,
            )
            .where(
                (WithdrawalDb.id == withdrawal_id)
                & WithdrawalDb.paid_at.is_(None)
                & (WithdrawalDb.amount >= amount)
            )
            .returning(WithdrawalDb.donator_id)
        )
        if result.rowcount != 1:
            raise NotFound(f"Withdrawal {withdrawal_id} does not exist or haven't enough money")
        donator_id = result.scalar()
        result = await self.execute(
            update(DonatorDb)
            .where(
                (DonatorDb.id == donator_id)
                & (DonatorDb.balance >= amount)
            )
            .values(balance=DonatorDb.balance - amount)
            .returning(DonatorDb.balance)
        )
        if result.rowcount != 1:
            raise NotFound(f"Donator {donator_id} does not exist or haven't enough money")
        await self.notify(f'withdrawal:{withdrawal_id}', Notification(id=withdrawal_id, status='OK'))
        await self.object_changed('donator', donator_id)
        return result.scalar()
