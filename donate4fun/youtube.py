import json
import logging
from functools import wraps
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ClientCreds, ServiceAccountCreds
from pydantic import BaseModel
from sqlalchemy.orm.exc import NoResultFound
from glom import glom

from .settings import settings
from .types import UnsupportedTarget, Url, ValidationError, EntityTooOld
from .db import DbSession, Database
from .db_youtube import YoutubeDbLib
from .models import YoutubeVideo, YoutubeChannel, Donation
from .core import register_command, app
from .api_utils import scrape_lightning_address, make_absolute_uri

ChannelId = str
VideoId = str
logger = logging.getLogger(__name__)


class UnsupportedYoutubeUrl(UnsupportedTarget):
    pass


class YoutubeVideoNotFound(ValidationError):
    pass


class YoutubeChannelNotFound(ValidationError):
    pass


class ChannelInfo(BaseModel):
    id: ChannelId
    title: str
    description: str
    thumbnail: Url | None
    banner: Url | None
    handle: str | None

    @classmethod
    def from_api(cls, data):
        return cls(
            id=data['id'],
            title=data['snippet']['title'],
            thumbnail=glom(data, 'snippet.thumbnails.medium.url', default=None),
            banner=glom(data, 'brandingSettings.image.bannerExternalUrl', default=None),
            description=glom(data, 'snippet.description', default=''),
            handle=glom(data, 'snippet.customUrl', default=None),
        )

    @property
    def url(self):
        return f'https://youtube.com/channel/{self.id}'


class VideoInfo(BaseModel):
    id: VideoId
    title: str
    thumbnail: Url
    default_audio_language: str


@dataclass
class YoutubeDonatee:
    channel_id: str | None = None
    video_id: str | None = None
    handle: str | None = None

    async def fetch(self, donation: Donation, db: DbSession):
        youtube_db = YoutubeDbLib(db)
        if self.video_id:
            donation.youtube_video = await query_or_fetch_youtube_video(video_id=self.video_id, db=youtube_db)
            donation.youtube_channel = donation.youtube_video.youtube_channel
        elif self.channel_id:
            donation.youtube_channel = await query_or_fetch_youtube_channel(channel_id=self.channel_id, db=youtube_db)
        elif self.handle:
            donation.youtube_channel = await query_or_fetch_youtube_channel(handle=self.handle, db=youtube_db)
        else:
            raise ValidationError("No YouTube donatee info")
        donation.lightning_address = donation.youtube_channel.lightning_address


def validate_youtube_url(parsed) -> YoutubeDonatee:
    parts = parsed.path.split('/')
    if parts[1] == 'watch':
        video_id = parse_qs(parsed.query)['v'][0]
        return YoutubeDonatee(video_id=video_id)
    elif parts[1] == 'shorts':
        return YoutubeDonatee(video_id=parts[2])
    elif parts[1] in ('channel', 'c'):
        return YoutubeDonatee(handle=parts[2])
    elif parts[1].startswith('@'):
        return YoutubeDonatee(handle=parts[1])
    elif parsed.hostname == 'youtu.be':
        raise UnsupportedYoutubeUrl("youtu.be urls are not supported")
    else:
        raise UnsupportedYoutubeUrl("Unrecognized YouTube URL")


def withyoutube(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with Aiogoogle(api_key=settings.youtube.api_key) as aiogoogle:
            youtube_v3 = await aiogoogle.discover("youtube", "v3")
            return await func(aiogoogle, youtube_v3, *args, **kwargs)
    return wrapper


@withyoutube
async def fetch_channel_by_owner(aiogoogle, youtube, creds: ClientCreds) -> ChannelInfo:
    req = youtube.channels.list(mine=True, part='snippet')
    res = await aiogoogle.as_user(req, user_creds=creds)
    items = res.get('items')
    if not items:
        raise YoutubeChannelNotFound
    return ChannelInfo.from_api(items[0])


def get_service_account_creds():
    return ServiceAccountCreds(
        scopes=[
            "https://www.googleapis.com/auth/youtube.read_only",
        ],
        **json.load(open(settings.youtube.service_account_key_file))
    )


async def query_or_fetch_youtube_video(video_id: str, db: YoutubeDbLib) -> YoutubeVideo:
    try:
        video: YoutubeVideo = await db.query_youtube_video(video_id=video_id)
        if should_refresh_channel(video.youtube_channel):
            video.youtube_channel = await query_or_fetch_youtube_channel(video.youtube_channel.channel_id, db)
    except NoResultFound:
        video: YoutubeVideo = await fetch_youtube_video(video_id, db)
        await db.save_youtube_video(video)
    return video


@withyoutube
async def fetch_youtube_video(aiogoogle, youtube, video_id: str, db: DbSession) -> YoutubeVideo:
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
        youtube_channel=await query_or_fetch_youtube_channel(channel_id=snippet['channelId'], db=db),
    )


def should_refresh_channel(channel: YoutubeChannel):
    return channel.last_fetched_at is None or channel.last_fetched_at < datetime.utcnow() - settings.youtube.refresh_timeout


async def query_or_fetch_youtube_channel(db: YoutubeDbLib, **params) -> YoutubeChannel:
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


@register_command
async def fetch_and_save_youtube_channel(channel_id: str):
    channel: YoutubeChannel = await fetch_youtube_channel(channel_id)
    async with Database(settings.db).session() as db:
        await db.save_youtube_channel(channel)


@withyoutube
async def search_for_youtube_channel(aiogoogle, youtube, handle: str) -> YoutubeChannel:
    """
    Until Google updates his YouTube API we ought to search by handle and then list for each result until we find the needed one.
    """
    req = youtube.search.list(q=handle, type='channel', part='snippet')
    res = await aiogoogle.as_api_key(req)
    total_results = res['pageInfo']['totalResults']
    if total_results == 0:
        raise YoutubeChannelNotFound(f"Could not find a YouTube channel for {handle}")
    for item in res['items']:
        channel: YoutubeChannel = await fetch_youtube_channel(item['id']['channelId'])
        if channel.handle == handle.lower():
            return channel
    else:
        raise YoutubeChannelNotFound(f"Could not find a YouTube channel for {handle}")


@register_command
@withyoutube
async def fetch_youtube_channel(aiogoogle, youtube, channel_id: str) -> YoutubeChannel:
    req = youtube.channels.list(id=channel_id, part='snippet,brandingSettings')
    res = await aiogoogle.as_api_key(req)
    total_results = res['pageInfo']['totalResults']
    if total_results == 0:
        raise YoutubeChannelNotFound(f"Could not find a YouTube channel for {channel_id}")
    if total_results > 1:
        raise YoutubeChannelNotFound(f"Found multiple YouTube channels for {channel_id}")
    items = res['items']
    if not items:
        raise YoutubeChannelNotFound("Invalid response from YouTube API")
    api_channel = ChannelInfo.from_api(items[0])
    return YoutubeChannel(
        channel_id=api_channel.id,
        title=api_channel.title,
        thumbnail_url=api_channel.thumbnail,
        last_fetched_at=datetime.utcnow(),
        banner_url=api_channel.banner,
        handle=api_channel.handle,
        lightning_address=scrape_lightning_address(api_channel.description),
    )


async def fetch_user_channel(code: str) -> ChannelInfo:
    async with Aiogoogle() as aiogoogle:
        full_user_creds = await aiogoogle.oauth2.build_user_creds(
            grant=code,
            client_creds=dict(
                redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='youtube')),
                **settings.youtube.oauth.dict(),
            ),
        )
    return await fetch_channel_by_owner(full_user_creds)


@withyoutube
async def find_comment(aiogoogle, youtube, video_id: str, comment: str) -> list[ChannelId]:
    req = youtube.commentThreads.list(part='snippet', videoId=video_id, searchTerms=comment)
    res = await aiogoogle.as_api_key(req)
    channels = []
    for item in res.get('items', []):
        snippet = item['snippet']['topLevelComment']['snippet']
        if snippet['textOriginal'] == comment:
            channels.append(snippet['authorChannelId']['value'])
    return channels
