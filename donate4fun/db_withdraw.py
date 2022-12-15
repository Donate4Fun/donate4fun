import math
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .types import NotFound
from .db_models import WithdrawalDb, DonatorDb
from .models import Notification
from .settings import settings


class WithdrawalDbMixin:
    async def create_withdrawal(self, donator: DonatorDb) -> WithdrawalDb:
        result = await self.execute(
            insert(WithdrawalDb)
            .values(
                created_at=datetime.utcnow(),
                donator_id=donator.id,
                amount=donator.balance - settings.fee_limit,
            )
            .returning(WithdrawalDb)
        )
        return result.fetchone()

    async def query_withdrawal(self, withdrawal_id: UUID) -> WithdrawalDb:
        result = await self.execute(
            select(WithdrawalDb)
            .where(WithdrawalDb.id == withdrawal_id)
        )
        return result.scalars().one()

    async def start_withdraw(self, withdrawal_id: UUID, amount: int, fee_msat: int) -> int:
        """
        Save withdrawal changes to db - this happens after the payment
        Returns new balance
        """
        result = await self.execute(
            update(WithdrawalDb)
            .values(
                paid_at=datetime.utcnow(),
                amount=amount,
                fee_msat=fee_msat,
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
        total_amount: int = math.ceil(amount + Decimal(fee_msat) / 1000)
        result = await self.execute(
            update(DonatorDb)
            .where(
                (DonatorDb.id == donator_id)
                & (DonatorDb.balance >= total_amount)
            )
            .values(balance=DonatorDb.balance - total_amount)
            .returning(DonatorDb.balance)
        )
        if result.rowcount != 1:
            raise NotFound(f"Donator {donator_id} does not exist or haven't enough money")
        await self.notify(f'withdrawal:{withdrawal_id}', Notification(id=withdrawal_id, status='OK'))
        await self.object_changed('donator', donator_id)
        return result.scalar()

    async def finish_withdraw(self, withdrawal_id: UUID, fee_msat: int):
        result = await self.execute(
            update(WithdrawalDb)
            .values(
                paid_at=datetime.utcnow(),
                fee_msat=fee_msat,
            )
            .where(WithdrawalDb.id == withdrawal_id)
            .returning(WithdrawalDb.donator_id)
        )
        donator_id = result.scalar()
        result = await self.execute(
            update(DonatorDb)
            .where(DonatorDb.id == donator_id)
            .values(balance=DonatorDb.balance + settings.fee_limit - math.ceil(fee_msat / 1000))
            .returning(DonatorDb.balance)
        )
