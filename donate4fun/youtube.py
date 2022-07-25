import json
import re
from functools import wraps
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ClientCreds, ServiceAccountCreds
from pydantic import BaseModel
from email_validator import validate_email

from .settings import settings
from .types import UnsupportedTarget, Url, ValidationError

ChannelId = str
VideoId = str


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
    channel: ChannelInfo
    video: VideoInfo | None


async def validate_youtube_url(parsed) -> YoutubeDonatee:
    parts = parsed.path.split('/')
    if parsed.path == '/watch':
        video_id = parse_qs(parsed.query)['v']
        return await fetch_donatee_by_video(video_id)
    elif parts[1] in ('channel', 'c'):
        part = parts[2]
        if part.startswith('UC'):
            channel_info = await fetch_channel(channel_id=part)
        else:
            channel_info = await fetch_channel(username=part)
        return YoutubeDonatee(
            channel=channel_info,
            video=None,
        )
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
    items = res['items']
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


@withyoutube
async def fetch_donatee_by_video(aiogoogle, youtube, video_id: str) -> YoutubeDonatee:
    req = youtube.videos.list(id=video_id, part='snippet')
    res = await aiogoogle.as_api_key(req)
    items = res['items']
    if not items:
        raise YoutubeVideoNotFound
    item = items[0]
    snippet = item['snippet']
    return YoutubeDonatee(
        channel=await fetch_channel(channel_id=snippet['channelId']),
        video=VideoInfo(
            id=item['id'],
            title=snippet['title'],
            thumbnail=snippet['thumbnails']['default']['url'],
            default_audio_language=snippet.get('defaultAudioLanguage', 'en'),
        )
    )


@withyoutube
async def fetch_channel(aiogoogle, youtube, channel_id: str | None = None, username: str | None = None) -> ChannelInfo:
    req = youtube.channels.list(id=channel_id, forUsername=username, part='snippet')
    res = await aiogoogle.as_api_key(req)
    if res['pageInfo']['totalResults'] == 0:
        raise YoutubeChannelNotFound("Invalid YouTube channel")
    items = res['items']
    if not items:
        raise YoutubeChannelNotFound
    return ChannelInfo.from_api(items[0])


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
        return await validate_youtube_url(parsed)
    else:
        raise UnsupportedTarget("URL is invalid")
