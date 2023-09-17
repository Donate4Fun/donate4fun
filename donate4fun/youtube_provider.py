import logging

from furl import furl
from sqlalchemy.orm.exc import NoResultFound

from .models import YoutubeChannel, YoutubeVideo, Donation
from .db import DbSession
from .db_youtube import YoutubeDbLib
from .social import SocialProvider
from .types import EntityTooOld, UnsupportedTarget
from .youtube import (
    should_refresh_channel, search_for_youtube_channel, fetch_youtube_channel,
    withyoutube, YoutubeVideoNotFound,
)

logger = logging.getLogger(__name__)


class UnsupportedYoutubeUrl(UnsupportedTarget):
    pass


class YoutubeProvider(SocialProvider):
    def wrap_db(self, db_session: DbSession) -> YoutubeDbLib:
        return YoutubeDbLib(db_session)

    async def query_or_fetch_account(self, db: YoutubeDbLib, **params) -> YoutubeChannel:
        try:
            channel: YoutubeChannel = await db.find_youtube_channel(**params)
            if should_refresh_channel(channel):
                logger.debug("youtube channel %s is too old, refreshing", channel)
                raise EntityTooOld
            return channel
        except (NoResultFound, EntityTooOld):
            channel: YoutubeChannel = (
                await fetch_youtube_channel(**params) if 'channel_id' in params else await search_for_youtube_channel(**params)
            )
            await db.save_account(channel)
            return channel

    async def query_or_fetch_video(self, video_id: str, db: YoutubeDbLib) -> YoutubeVideo:
        try:
            video: YoutubeVideo = await db.query_youtube_video(video_id=video_id)
            if should_refresh_channel(video.youtube_channel):
                video.youtube_channel = await YoutubeProvider().query_or_fetch_account(video.youtube_channel.channel_id, db)
        except NoResultFound:
            video: YoutubeVideo = await self.fetch_video(video_id, db)
            await db.save_youtube_video(video)
        return video

    @withyoutube
    async def fetch_video(self, video_id: str, db: DbSession, aiogoogle, youtube) -> YoutubeVideo:
        req = youtube.videos.list(id=video_id, part='snippet')
        res = await aiogoogle.as_api_key(req)
        items = res['items']
        if not items:
            raise YoutubeVideoNotFound
        item = items[0]
        snippet = item['snippet']
        return YoutubeVideo(
            video_id=item['id'],
            title=snippet['title'],
            thumbnail_url=snippet['thumbnails']['default']['url'],
            default_audio_language=snippet.get('defaultAudioLanguage', 'en'),
            youtube_channel=await self.query_or_fetch_account(channel_id=snippet['channelId'], db=db),
        )

    async def get_account_path(self, account: YoutubeChannel) -> str:
        return f'/youtube/{account.id}'

    async def apply_target(self, donation: Donation, target: furl, db_session: DbSession):
        parts = target.path.segments
        handle = None
        video_id = None
        channel_id = None
        match parts[0]:
            case 'watch':
                video_id = target.query.params['v']
            case 'shorts':
                video_id = parts[1]
            case 'channel' | 'c':
                channel_id = parts[1]
            case s if s.startswith('@'):
                handle = s
            case _:
                raise UnsupportedYoutubeUrl("Unrecognized YouTube URL")

        youtube_db = self.wrap_db(db_session)
        if video_id:
            donation.youtube_video = await self.query_or_fetch_video(video_id=video_id, db=youtube_db)
            self.set_donation_receiver(donation, donation.youtube_video.youtube_channel)
        elif channel_id:
            self.set_donation_receiver(donation, await self.query_or_fetch_account(channel_id=channel_id, db=youtube_db))
        elif handle:
            self.set_donation_receiver(donation, await self.query_or_fetch_account(handle=handle, db=youtube_db))
        donation.lightning_address = donation.youtube_channel.lightning_address

    def set_donation_receiver(self, donation: Donation, receiver: YoutubeChannel):
        donation.youtube_channel = receiver
