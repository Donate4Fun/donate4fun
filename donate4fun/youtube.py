import json
import logging
import re
from functools import wraps
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ClientCreds, ServiceAccountCreds
from pydantic import BaseModel
from email_validator import validate_email
from sqlalchemy.orm.exc import NoResultFound

from .settings import settings
from .types import UnsupportedTarget, Url, ValidationError
from .db import DbSession
from .models import YoutubeVideo, YoutubeChannel, Donation

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
    thumbnail: Url

    @classmethod
    def from_api(cls, data):
        return cls(
            id=data['id'],
            title=data['snippet']['title'],
            thumbnail=data['snippet']['thumbnails']['medium']['url'],
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


def validate_youtube_url(parsed) -> YoutubeDonatee:
    parts = parsed.path.split('/')
    if parts[1] == 'watch':
        video_id = parse_qs(parsed.query)['v'][0]
        return YoutubeDonatee(video_id=video_id)
    elif parts[1] == 'shorts':
        return YoutubeDonatee(video_id=parts[2])
    elif parts[1] in ('channel', 'c'):
        return YoutubeDonatee(channel_id=parts[2])
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
    channel = items[0]
    snippet = channel['snippet']
    return ChannelInfo(
        id=channel['id'],
        title=snippet['title'],
        thumbnail=snippet['thumbnails']['medium']['url'],
    )


def get_service_account_creds():
    return ServiceAccountCreds(
        scopes=[
            "https://www.googleapis.com/auth/youtube.read_only",
        ],
        **json.load(open(settings.youtube.service_account_key_file))
    )


async def query_or_fetch_youtube_video(video_id: str, db: DbSession):
    try:
        return await db.query_youtube_video(video_id=video_id)
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


class ChannelIsTooOld(Exception):
    pass


async def query_or_fetch_youtube_channel(channel_id: str, db: DbSession) -> YoutubeChannel:
    try:
        channel: YoutubeChannel = await db.find_youtube_channel(channel_id=channel_id)
        if channel.last_fetched_at is None or channel.last_fetched_at < datetime.utcnow() - settings.youtube.refresh_timeout:
            logger.debug("youtube channel %s is too old, refreshing", channel)
            raise ChannelIsTooOld
        return channel
    except (NoResultFound, ChannelIsTooOld):
        channel: YoutubeChannel = await fetch_youtube_channel(channel_id)
        await db.save_youtube_channel(channel)
        return channel


@withyoutube
async def fetch_youtube_channel(aiogoogle, youtube, channel_id: str) -> YoutubeChannel:
    if not channel_id.startswith('UC'):
        username = channel_id
        channel_id = None
    else:
        username = None
    req = youtube.channels.list(id=channel_id, forUsername=username, part='snippet')
    res = await aiogoogle.as_api_key(req)
    if res['pageInfo']['totalResults'] == 0:
        raise YoutubeChannelNotFound("Invalid YouTube channel")
    items = res['items']
    if not items:
        raise YoutubeChannelNotFound
    api_channel = ChannelInfo.from_api(items[0])
    return YoutubeChannel(
        channel_id=api_channel.id,
        title=api_channel.title,
        thumbnail_url=api_channel.thumbnail,
        last_fetched_at=datetime.utcnow(),
    )


async def fetch_user_channel(request, code: str) -> ChannelInfo:
    async with Aiogoogle() as aiogoogle:
        full_user_creds = await aiogoogle.oauth2.build_user_creds(
            grant=code,
            client_creds=dict(
                redirect_uri=request.app.url_path_for('auth_google').make_absolute_url(settings.youtube.oauth.redirect_base_url),
                **settings.youtube.oauth.dict(),
            ),
        )
    return await fetch_channel_by_owner(full_user_creds)


async def validate_target(target: str):
    if re.match(r'https?://.+', target):
        return await validate_target_url(target)
    return validate_email(target).email


async def validate_target_url(target: Url):
    parsed = urlparse(target)
    if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be']:
        return validate_youtube_url(parsed)
    elif parsed.hostname in ['twitter.com', 'www.twitter.com']:
        return validate_twitter_url(parsed)
    else:
        raise UnsupportedTarget("URL is invalid")


@dataclass
class TwitterDonatee:
    author_handle: str
    tweet_id: str | None = None


class UnsupportedTwitterUrl(Exception):
    pass


def validate_twitter_url(parsed) -> TwitterDonatee:
    parts = parsed.path.split('/')
    if len(parts) == 2:
        return TwitterDonatee(author_handle=parts[1])
    elif len(parts) == 4 and parts[2] == 'status':
        return TwitterDonatee(tweet_id=parts[3], author_handle=parts[1])
    else:
        raise UnsupportedTwitterUrl


async def apply_target(donation: Donation, target: str, db: DbSession):
    donatee = await validate_target(target)

    if isinstance(donatee, YoutubeDonatee):
        if donatee.video_id:
            donation.youtube_video = await query_or_fetch_youtube_video(video_id=donatee.video_id, db=db)
            donation.youtube_channel = donation.youtube_video.youtube_channel
        elif donatee.channel_id:
            donation.youtube_channel = await query_or_fetch_youtube_channel(channel_id=donatee.channel_id, db=db)
    elif isinstance(donatee, TwitterDonatee):
        donation.twitter_author = await db.get_or_create_twitter_author(donatee.author_handle)
        donation.twitter_tweet_id = await db.get_or_create_twitter_tweet(donatee.tweet_id)
    else:
        raise NotImplementedError


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
