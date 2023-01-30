import logging
import math
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc, update, func, case, true
from sqlalchemy.dialects.postgresql import insert

from .models import Donation, DonatorStats, Notification
from .types import RequestHash, NotEnoughBalance, ValidationError
from .db import DbSessionWrapper
from .db_models import (
    DonatorDb, DonationDb, YoutubeChannelDb, TwitterAuthorDb,
    YoutubeChannelLink, TwitterAuthorLink,
)
from .db_youtube import YoutubeDbLib
from .db_twitter import TwitterDbLib
from .db_github import GithubDbLib

logger = logging.getLogger(__name__)


class UnableToCancelDonation(ValidationError):
    pass


class DonationsDbLib(DbSessionWrapper):
    async def query_donations(self, where, limit: int = 20, offset: int = 0):
        result = await self.execute(
            select(DonationDb)
            .where(where)
            .order_by(desc(func.coalesce(DonationDb.paid_at, DonationDb.created_at)))
            .limit(limit)
            .offset(offset)
        )
        return [Donation.from_orm(obj) for obj in result.unique().scalars()]

    async def lock_donation(self, r_hash: RequestHash) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(DonationDb.r_hash == r_hash.as_base64)
            .with_for_update(of=DonationDb)
        )
        return Donation.from_orm(result.scalar_one())

    async def query_donation(self, id: UUID) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(DonationDb.id == id)
        )
        return Donation.from_orm(result.scalar_one())

    async def create_donation(self, donation: Donation):
        donation.created_at = datetime.utcnow()
        await self.execute(
            insert(DonationDb)
            .values(
                id=donation.id,
                created_at=donation.created_at,
                donator_id=donation.donator and donation.donator.id,
                amount=donation.amount,
                lightning_address=donation.lightning_address,
                r_hash=donation.r_hash and donation.r_hash.as_base64,
                transient_r_hash=donation.transient_r_hash and donation.transient_r_hash.as_base64,
                receiver_id=donation.receiver and donation.receiver.id,
                youtube_channel_id=donation.youtube_channel and donation.youtube_channel.id,
                youtube_video_id=donation.youtube_video and donation.youtube_video.id,
                twitter_account_id=donation.twitter_account and donation.twitter_account.id,
                twitter_tweet_id=donation.twitter_tweet and donation.twitter_tweet.id,
                github_user_id=donation.github_user and donation.github_user.id,
                donator_twitter_account_id=donation.donator_twitter_account and donation.donator_twitter_account.id,
            )
        )
        return donation

    async def update_donation(self, donation_id: UUID, r_hash: RequestHash):
        await self.execute(
            update(DonationDb)
            .values(r_hash=r_hash.as_base64)
            .where(DonationDb.id == donation_id)
        )

    async def cancel_donation(self, donation_id: UUID) -> Donation:
        resp = await self.execute(
            update(DonationDb)
            .values(
                cancelled_at=datetime.utcnow(),
            )
            .where(
                DonationDb.claimed_at.is_(None)
                & DonationDb.cancelled_at.is_(None)
                & (DonationDb.id == donation_id)
            )
            .returning(*DonationDb.__table__.columns)
        )
        donation: DonationDb = resp.fetchone()
        if donation is None:
            raise UnableToCancelDonation("Donation could not be cancelled")
        if donation.paid_at is not None:
            await self.update_balance_for_donation(donation, -donation.amount)
        return Donation(**donation)

    async def donation_paid(
        self, donation_id: UUID, amount: int, paid_at: datetime, fee_msat: int = None, claimed_at: datetime = None,
    ):
        resp = await self.execute(
            update(DonationDb)
            .where((DonationDb.id == donation_id) & DonationDb.paid_at.is_(None))
            .values(
                amount=amount,
                paid_at=paid_at,
                fee_msat=fee_msat,
                claimed_at=claimed_at,
            )
            .returning(*DonationDb.__table__.columns)
        )
        donation: DonationDb = resp.fetchone()
        if donation is None:
            # Row could be already updated in another replica
            logger.warning(f"Donation {donation_id} was already handled, skipping")
            return
        await self.update_balance_for_donation(donation, donation.amount)

    async def update_balance_for_donation(self, donation: DonationDb, amount: int):
        """
        amount - balance diff in sats, it's positive when donation is completed
                 and negative when donation is cancelled
        """
        # If donation was made to a lightning address then do not change social accounts' balances (it's already claimed)
        balance_amount = amount if donation.claimed_at is None else 0
        if donation.youtube_channel_id:
            social_db = YoutubeDbLib(self)
        elif donation.twitter_account_id:
            social_db = TwitterDbLib(self)
        elif donation.github_user_id:
            social_db = GithubDbLib(self)
        elif donation.receiver_id:
            social_db = None
            resp = await self.execute(
                update(DonatorDb)
                .values(balance=DonatorDb.balance + balance_amount)
                .where(DonatorDb.id == donation.receiver_id)
                .returning(DonatorDb.balance)
            )
            if resp.fetchone().balance < 0:
                raise NotEnoughBalance(f"Donator {donation.receiver_id} hasn't enough money")
            await self.object_changed('donator', donation.receiver_id)
        else:
            raise ValueError(f"Donation {donation.id} has no target")
        if social_db:
            await social_db.update_balance_for_donation(balance_diff=balance_amount, total_diff=amount, donation=donation)
        if (donation.r_hash is None) == (donation.lightning_address is None):
            # r_hash   | lightning_address | description                     | action
            # ==========================================================================================
            # None     | not None          | from an external wallet to      | do nothing
            #          |                   |   an external lightning address |
            # None     | None              | internal donation               | change both balances
            # not None | None              | from an external wallet to local|
            #          |                   |   balance                       | increase receiver balance
            # not None | not None          | from an internal balance to     | decrease donator balance
            #          |                   |   an external lightning address |
            resp = await self.execute(
                update(DonatorDb)
                .where((DonatorDb.id == donation.donator_id))
                .values(balance=DonatorDb.balance - amount - math.ceil((donation.fee_msat or 0) / 1000))
                .returning(DonatorDb.balance)
            )
            if resp.fetchone().balance < 0:
                raise NotEnoughBalance(f"Donator {donation.donator_id} hasn't enough money")

        await self.object_changed('donation', donation.id)
        await self.notify('donations', Notification(id=donation.id, status='OK'))
        if donation.donator_id is not None:
            await self.object_changed('donator', donation.donator_id)

    async def query_donator_stats(self, donator_id: UUID):
        received_sq = received_donations_subquery(donator_id)
        received_stats_sq = select(
            func.coalesce(func.sum(received_sq.c.amount), 0).label('total_received')
        ).where(
            received_sq.c.receiver_id.is_(None)
            | (received_sq.c.receiver_id != received_sq.c.donator_id)
        ).subquery()

        sent_sq = sent_donations_subquery(donator_id)
        sent_stats_sq = select(
            func.coalesce(func.sum(sent_sq.c.amount), 0).label('total_donated'),
            func.coalesce(func.sum(case(
                (sent_sq.c.claimed_at.is_(None), 0),
                else_=sent_sq.c.amount,
            )), 0).label('total_claimed'),
        ).where(
            sent_sq.c.receiver_id.is_(None)
            | (sent_sq.c.receiver_id != sent_sq.c.donator_id)
        ).subquery()

        result = await self.execute(
            select(received_stats_sq.c.total_received, sent_stats_sq.c.total_claimed, sent_stats_sq.c.total_donated)
            .join(sent_stats_sq, true())
        )
        return DonatorStats.from_orm(result.fetchone())


def sent_donations_subquery(donator_id: UUID):
    return select(
        DonationDb
    ).where(
        DonationDb.paid_at.isnot(None)
        & DonationDb.cancelled_at.is_(None)
        & (DonationDb.donator_id == donator_id)
        & (
            DonationDb.receiver_id.is_(None) |
            (DonationDb.donator_id != DonationDb.receiver_id)
        )
    ).subquery()


def received_donations_subquery(donator_id: UUID):
    return select(
        DonationDb
    ).outerjoin(
        DonationDb.youtube_channel
    ).outerjoin(
        YoutubeChannelDb.links
    ).outerjoin(
        DonationDb.twitter_account
    ).outerjoin(
        TwitterAuthorDb.links
    ).where(
        DonationDb.paid_at.isnot(None)
        & DonationDb.cancelled_at.is_(None)
        & (
            (YoutubeChannelLink.donator_id == donator_id)
            | (TwitterAuthorLink.donator_id == donator_id)
            | (DonationDb.receiver_id == donator_id)
        )
    ).subquery()
