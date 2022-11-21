import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import Donation, Notification, YoutubeNotification
from .types import RequestHash, NotEnoughBalance
from .db_models import DonatorDb, DonationDb, YoutubeChannelDb, YoutubeVideoDb, TwitterAuthorDb

logger = logging.getLogger(__name__)


class DonationsDbMixin:
    async def query_donations(self, where, limit=20):
        result = await self.execute(
            select(DonationDb)
            .where(where)
            .order_by(desc(func.coalesce(DonationDb.paid_at, DonationDb.created_at)))
            .limit(limit)
        )
        return [Donation.from_orm(obj) for obj in result.unique().scalars()]

    async def query_donation(self, *, r_hash: RequestHash | None = None, id: UUID | None = None) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(
                (DonationDb.r_hash == r_hash.as_base64) if r_hash else (DonationDb.id == id)
            )
        )
        data = result.scalars().one()
        return Donation.from_orm(data)

    async def create_donation(self, donation: Donation):
        donation.created_at = datetime.utcnow()
        await self.execute(
            insert(DonationDb)
            .values(
                id=donation.id,
                created_at=donation.created_at,
                donator_id=donation.donator.id,
                amount=donation.amount,
                r_hash=donation.r_hash and donation.r_hash.as_base64,
                receiver_id=donation.receiver and donation.receiver.id,
                youtube_channel_id=donation.youtube_channel and donation.youtube_channel.id,
                youtube_video_id=donation.youtube_video and donation.youtube_video.id,
                twitter_author_id=donation.twitter_account and donation.twitter_account.id,
                twitter_tweet_id=donation.twitter_tweet and donation.twitter_tweet.id,
            )
        )
        return donation

    async def update_donation(self, donation_id: UUID, r_hash: RequestHash):
        await self.execute(
            update(DonationDb)
            .values(r_hash=r_hash.as_base64)
            .where(DonationDb.id == donation_id)
        )

    async def cancel_donation(self, donation_id: UUID) -> RequestHash:
        """
        I'm not sure that this method is needed.
        """
        resp = await self.execute(
            update(DonationDb)
            .values(
                cancelled_at=datetime.utcnow(),
            )
            .where(
                DonationDb.id == donation_id,
            )
            .returning(DonationDb.r_hash)
        )
        return resp.scalar()

    async def donation_paid(self, donation_id: UUID, amount: int, paid_at: datetime):
        resp = await self.execute(
            update(DonationDb)
            .where((DonationDb.id == donation_id) & DonationDb.paid_at.is_(None))
            .values(
                amount=amount,
                paid_at=paid_at,
            )
            .returning(
                DonationDb.id,
                DonationDb.donator_id,
                DonationDb.youtube_channel_id,
                DonationDb.youtube_video_id,
                DonationDb.twitter_author_id,
                DonationDb.receiver_id,
                DonationDb.r_hash,
            )
        )
        row = resp.fetchone()
        if row is None:
            # Row could be already updated in another replica
            logger.debug(f"Donation {donation_id} was already handled, skipping")
            return

        if row.youtube_channel_id:
            await self.execute(
                update(YoutubeChannelDb)
                .values(
                    balance=YoutubeChannelDb.balance + amount,
                    total_donated=YoutubeChannelDb.total_donated + amount,
                )
                .where(YoutubeChannelDb.id == row.youtube_channel_id)
            )
            if row.youtube_video_id:
                video_update_resp = await self.execute(
                    update(YoutubeVideoDb)
                    .values(total_donated=YoutubeVideoDb.total_donated + amount)
                    .where(YoutubeVideoDb.id == row.youtube_video_id)
                    .returning(YoutubeVideoDb.video_id, YoutubeVideoDb.total_donated)
                )
                vid, total_donated = video_update_resp.fetchone()
                notification = YoutubeNotification(id=row.youtube_video_id, vid=vid, status='OK', total_donated=total_donated)
                await self.notify(f'youtube-video:{row.youtube_video_id}', notification)
                await self.notify(f'youtube-video-by-vid:{vid}', notification)
        elif row.twitter_author_id:
            await self.execute(
                update(TwitterAuthorDb)
                .values(
                    balance=TwitterAuthorDb.balance + amount,
                    total_donated=TwitterAuthorDb.total_donated + amount,
                )
                .where(TwitterAuthorDb.id == row.twitter_author_id)
            )
        elif row.receiver_id:
            await self.execute(
                update(DonatorDb)
                .values(balance=DonatorDb.balance + amount)
                .where(DonatorDb.id == row.receiver_id)
            )
            await self.notify(f'donator:{row.receiver_id}', Notification(id=row.receiver_id, status='OK'))
        else:
            raise ValueError(f"Donation has no target: {row.donation_id}")
        if row.r_hash is None:
            # donation without invoice, use donator balance
            resp = await self.execute(
                update(DonatorDb)
                .where((DonatorDb.id == row.donator_id) & (DonatorDb.balance >= amount))
                .values(balance=DonatorDb.balance - amount)
            )
            if resp.rowcount != 1:
                raise NotEnoughBalance(f"Donator {row.donator_id} hasn't enough money")
        await self.notify(f'donation:{row.donation_id}', Notification(id=row.donation_id, status='OK'))
