from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import Donator, YoutubeChannel, YoutubeVideo, YoutubeChannelOwned
from .db_models import YoutubeChannelDb, YoutubeVideoDb, YoutubeChannelLink, DonationDb


class YoutubeDbMixin:
    async def query_youtube_channel(self, youtube_channel_id: UUID, owner_id: UUID | None = None) -> YoutubeChannelOwned:
        owner_links = select(YoutubeChannelLink).where(YoutubeChannelLink.donator_id == owner_id).subquery()
        resp = await self.execute(
            select(*YoutubeChannelDb.__table__.c, owner_links.c.donator_id.is_not(None).label('is_my'))
            .join(
                owner_links,
                onclause=YoutubeChannelDb.id == owner_links.c.youtube_channel_id,
                isouter=True,
            )
            .where(YoutubeChannelDb.id == youtube_channel_id)
        )
        return YoutubeChannelOwned.from_orm(resp.one())

    async def find_youtube_channel(self, channel_id: str) -> YoutubeChannel:
        resp = await self.execute(
            select(YoutubeChannelDb)
            .where(YoutubeChannelDb.channel_id == channel_id)
        )
        return YoutubeChannel.from_orm(resp.scalars().one())

    async def query_youtube_channels(self) -> list[YoutubeChannel]:
        resp = await self.execute(
            select(YoutubeChannelDb)
        )
        return [YoutubeChannel.from_orm(data) for data in resp.scalars()]

    async def lock_youtube_channel(self, youtube_channel_id: UUID) -> YoutubeChannel:
        result = await self.execute(
            select(YoutubeChannelDb)
            .with_for_update(of=YoutubeChannelDb)
            .where(YoutubeChannelDb.id == youtube_channel_id)
        )
        return YoutubeChannel.from_orm(result.scalars().one())

    async def save_youtube_channel(self, youtube_channel: YoutubeChannel):
        resp = await self.execute(
            insert(YoutubeChannelDb)
            .values(youtube_channel.dict())
            .on_conflict_do_update(
                index_elements=[YoutubeChannelDb.channel_id],
                set_={
                    YoutubeChannelDb.title: youtube_channel.title,
                    YoutubeChannelDb.thumbnail_url: youtube_channel.thumbnail_url,
                    YoutubeChannelDb.banner_url: youtube_channel.banner_url,
                },
                where=(
                    (func.coalesce(YoutubeChannelDb.title, '') != youtube_channel.title)
                    | (func.coalesce(YoutubeChannelDb.thumbnail_url, '') != youtube_channel.thumbnail_url)
                    | (func.coalesce(YoutubeChannelDb.banner_url, '') != youtube_channel.banner_url)
                ),
            )
            .returning(YoutubeChannelDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(YoutubeChannelDb.id).where(YoutubeChannelDb.channel_id == youtube_channel.channel_id)
            )
            id_ = resp.scalar()
        youtube_channel.id = id_

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

    async def link_youtube_channel(self, youtube_channel: YoutubeChannel, donator: Donator) -> bool:
        result = await self.execute(
            insert(YoutubeChannelLink)
            .values(
                youtube_channel_id=youtube_channel.id,
                donator_id=donator.id,
            )
            .on_conflict_do_nothing()
        )
        return result.rowcount == 1

    async def query_youtube_video(self, video_id: str) -> YoutubeVideo:
        resp = await self.execute(
            select(YoutubeVideoDb)
            .where(YoutubeVideoDb.video_id == video_id)
        )
        return YoutubeVideo.from_orm(resp.scalars().one())

    async def query_donator_youtube_channels(self, donator_id: UUID) -> list[YoutubeChannel]:
        result = await self.execute(
            select(YoutubeChannelDb)
            .join(YoutubeChannelLink, YoutubeChannelDb.id == YoutubeChannelLink.youtube_channel_id)
            .where(YoutubeChannelLink.donator_id == donator_id)
        )
        return [YoutubeChannel.from_orm(obj) for obj in result.unique().scalars()]

    async def transfer_youtube_donations(self, youtube_channel: YoutubeChannel, donator: Donator) -> int:
        """
        Transfers money from YouTube channel balance to donator balance
        Returns amount transferred
        """
        result = await self.execute(
            select(YoutubeChannelDb.balance)
            .with_for_update()
            .where(YoutubeChannelDb.id == youtube_channel.id)
        )
        amount: int = result.scalar()
        donations_filter = DonationDb.youtube_channel_id == youtube_channel.id
        await self.start_transfer(
            donator=donator,
            amount=amount,
            donations_filter=donations_filter,
            youtube_channel_id=youtube_channel.id,
        )
        await self.execute(
            update(YoutubeChannelDb)
            .values(balance=YoutubeChannelDb.balance - amount)
            .where(YoutubeChannelDb.id == youtube_channel.id)
        )
        await self.finish_transfer(amount=amount, donator=donator, donations_filter=donations_filter)
        return amount
