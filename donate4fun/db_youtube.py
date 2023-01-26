from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import Donator, YoutubeChannel, YoutubeVideo, YoutubeChannelOwned, YoutubeNotification
from .db_models import YoutubeChannelDb, YoutubeVideoDb, YoutubeChannelLink, DonationDb
from .db_social import SocialDbWrapper
from .types import Satoshi


class YoutubeDbLib(SocialDbWrapper):
    db_model = YoutubeChannelDb
    link_db_model = YoutubeChannelLink
    donation_column = 'youtube_channel_id'
    owned_model = YoutubeChannelOwned
    model = YoutubeChannel
    name = 'youtube'
    donation_field = 'youtube_channel'

    async def query_youtube_channel(self, *, owner_id: UUID | None = None, **filter_by) -> YoutubeChannelOwned:
        return YoutubeChannelOwned.from_orm(
            await self.query_social_account(YoutubeChannelLink, owner_id=owner_id, **filter_by)
        )

    async def find_youtube_channel(self, **filter_by) -> YoutubeChannel:
        resp = await self.execute(
            select(YoutubeChannelDb)
            .filter_by(**filter_by)
        )
        return YoutubeChannel.from_orm(resp.scalars().one())

    async def query_youtube_channels(self, *filters) -> list[YoutubeChannel]:
        resp = await self.execute(
            select(YoutubeChannelDb)
            .where(*filters)
        )
        return [YoutubeChannel.from_orm(data) for data in resp.scalars()]

    async def lock_youtube_channel(self, youtube_channel_id: UUID) -> YoutubeChannel:
        result = await self.execute(
            select(YoutubeChannelDb)
            .with_for_update(of=YoutubeChannelDb)
            .where(YoutubeChannelDb.id == youtube_channel_id)
        )
        return YoutubeChannel.from_orm(result.scalars().one())

    async def save_youtube_video(self, youtube_video: YoutubeVideo):
        resp = await self.execute(
            insert(YoutubeVideoDb)
            .values(dict(
                youtube_channel_id=youtube_video.youtube_channel.id,
                **{
                    key: value
                    for key, value in youtube_video.dict().items()
                    if key != 'youtube_channel'
                },
            ))
            .on_conflict_do_update(
                index_elements=[YoutubeVideoDb.video_id],
                set_={
                    YoutubeVideoDb.title: youtube_video.title,
                    YoutubeVideoDb.thumbnail_url: youtube_video.thumbnail_url,
                },
                where=(
                    (func.coalesce(YoutubeVideoDb.title, '') != youtube_video.title)
                    | (func.coalesce(YoutubeVideoDb.thumbnail_url, '') != youtube_video.thumbnail_url)
                ),
            )
            .returning(YoutubeVideoDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(YoutubeVideoDb.id).where(YoutubeVideoDb.video_id == youtube_video.video_id)
            )
            id_ = resp.scalar()
        youtube_video.id = id_

    async def query_youtube_video(self, video_id: str) -> YoutubeVideo:
        resp = await self.execute(
            select(YoutubeVideoDb)
            .where(YoutubeVideoDb.video_id == video_id)
        )
        return YoutubeVideo.from_orm(resp.scalars().one())

    async def query_donator_youtube_channels(self, donator_id: UUID) -> list[YoutubeChannelOwned]:
        result = await self.execute(
            select(*YoutubeChannelDb.__table__.columns, func.bool_or(YoutubeChannelLink.via_oauth).label('via_oauth'))
            .join(YoutubeChannelLink, YoutubeChannelDb.id == YoutubeChannelLink.youtube_channel_id)
            .where(YoutubeChannelLink.donator_id == donator_id)
            .group_by(YoutubeChannelDb.id)
        )
        return [YoutubeChannelOwned(**obj) for obj in result.all()]

    async def transfer_youtube_donations(self, youtube_channel: YoutubeChannel, donator: Donator) -> int:
        return await self.transfer_social_donations(DonationDb.youtube_channel, youtube_channel, donator)

    async def update_balance_for_donation(self, balance_diff: Satoshi, total_diff: Satoshi, donation: DonationDb) -> Satoshi:
        await super().update_balance_for_donation(balance_diff, total_diff, donation)
        if donation.youtube_video_id:
            video_update_resp = await self.execute(
                update(YoutubeVideoDb)
                .values(total_donated=YoutubeVideoDb.total_donated + total_diff)
                .where(YoutubeVideoDb.id == donation.youtube_video_id)
                .returning(YoutubeVideoDb.video_id, YoutubeVideoDb.total_donated)
            )
            vid, total_donated = video_update_resp.fetchone()
            notification = YoutubeNotification(id=donation.youtube_video_id, vid=vid, status='OK', total_donated=total_donated)
            await self.object_changed('youtube-video', donation.youtube_video_id, notification)
            await self.object_changed('youtube-video-by-vid', vid, notification)
