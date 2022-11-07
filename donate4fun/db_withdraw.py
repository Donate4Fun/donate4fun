from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .types import NotFound
from .db_models import WithdrawalDb, YoutubeChannelDb


class WithdrawalDbMixin:
    async def create_withdrawal(self, youtube_channel_id: UUID, donator_id: UUID) -> UUID:
        result = await self.execute(
            insert(WithdrawalDb)
            .values(dict(
                donator_id=donator_id,
                youtube_channel_id=youtube_channel_id,
                created_at=datetime.utcnow(),
            ))
            .returning(WithdrawalDb.id)
        )
        return result.scalars().one()

    async def query_withdrawal(self, withdrawal_id: UUID) -> WithdrawalDb:
        result = await self.execute(
            select(WithdrawalDb)
            .where(WithdrawalDb.id == withdrawal_id)
        )
        return result.scalars().one()

    async def lock_withdrawal(self, withdrawal_id: UUID):
        result = await self.execute(
            select(WithdrawalDb)
            .with_for_update(of=WithdrawalDb)
            .where(
                (WithdrawalDb.id == withdrawal_id)
                & WithdrawalDb.paid_at.is_(None)
            )
        )
        return result.scalars().one()

    async def withdraw(self, withdrawal_id: UUID, youtube_channel_id: UUID, amount: int) -> int:
        """
        return new balance
        """
        result = await self.execute(
            update(YoutubeChannelDb)
            .where((YoutubeChannelDb.id == youtube_channel_id) & (YoutubeChannelDb.balance >= amount))
            .values(balance=YoutubeChannelDb.balance - amount)
            .returning(YoutubeChannelDb.balance)
        )
        new_balance = result.scalars().one()
        result = await self.execute(
            update(WithdrawalDb)
            .values(
                paid_at=datetime.utcnow(),
                amount=amount,
            )
            .where(WithdrawalDb.id == withdrawal_id)
        )
        if result.rowcount != 1:
            raise NotFound(f"Withdrawal {withdrawal_id} does not exist")
        return new_balance
