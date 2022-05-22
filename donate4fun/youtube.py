import json
from functools import wraps
from dataclasses import dataclass
from urllib.parse import parse_qs, urlunparse

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ClientCreds, ServiceAccountCreds
from .settings import settings
from .models import UnsupportedTarget, Url, ValidationError

ChannelId = str


class UnsupportedYoutubeUrl(UnsupportedTarget):
    pass


class YoutubeVideoNotFound(ValidationError):
    pass


class YoutubeChannelNotFound(ValidationError):
    pass


@dataclass
class YoutubeDonatee:
    name: str
    url: Url
    trigger: Url | None
    thumbnail: Url | None


@dataclass
class ChannelInfo:
    id: ChannelId
    title: str
    thumbnail: Url

    @classmethod
    def from_api(cls, data):
        return cls(
            id=data['id'],
            title=data['snippet']['title'],
            thumbnail=data['snippet']['thumbnails']['default']['url'],
        )

    @property
    def url(self):
        return f'https://youtube.com/channel/{self.id}'


async def validate_youtube_url(parsed) -> YoutubeDonatee:
    parts = parsed.path.split('/')
    trigger = None
    if parsed.path == '/watch':
        video_id = parse_qs(parsed.query)['v']
        channel_info = await fetch_channel_by_video(video_id)
        trigger = urlunparse(parsed)
    elif parts[1] == 'channel':
        part = parts[2]
        if part[:3] == 'UC_':
            channel_info = await fetch_channel(channel_id=part)
        else:
            channel_info = await fetch_channel(username=part)
    elif parsed.hostname == 'youtu.be':
        raise UnsupportedYoutubeUrl
    else:
        raise UnsupportedYoutubeUrl
    return YoutubeDonatee(
        name=channel_info.title,
        url=channel_info.url,
        thumbnail=channel_info.thumbnail,
        trigger=trigger,
    )


def withyoutube(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with Aiogoogle(api_key=settings().youtube.api_key) as aiogoogle:
            youtube_v3 = await aiogoogle.discover("youtube", "v3")
            return await func(aiogoogle, youtube_v3, *args, **kwargs)
    return wrapper


@withyoutube
async def fetch_channel_by_owner(aiogoogle, youtube, creds: ClientCreds) -> ChannelInfo:
    req = youtube.channels.list(mine=True, part='id')
    res = await aiogoogle.as_user(req, user_creds=creds)
    items = res['items']
    if not items:
        raise YoutubeChannelNotFound
    snippet = items[0]['snippet']
    return ChannelInfo(
        id=snippet['id'],
        title=snippet['title'],
    )


def get_service_account_creds():
    return ServiceAccountCreds(
        scopes=[
            "https://www.googleapis.com/auth/youtube.read_only",
        ],
        **json.load(open(settings().youtube.service_account_key_file))
    )


@withyoutube
async def fetch_channel_by_video(aiogoogle, youtube, video_id: str) -> ChannelInfo:
    req = youtube.videos.list(id=video_id, part='snippet')
    res = await aiogoogle.as_api_key(req)
    items = res['items']
    if not items:
        raise YoutubeVideoNotFound
    return await fetch_channel(channel_id=items[0]['snippet']['channelId'])


@withyoutube
async def fetch_channel(aiogoogle, youtube, channel_id: str | None = None, username: str | None = None) -> ChannelInfo:
    req = youtube.channels.list(id=channel_id, forUsername=username, part='snippet')
    res = await aiogoogle.as_api_key(req)
    items = res['items']
    if not items:
        raise YoutubeChannelNotFound
    return ChannelInfo.from_api(items[0])


async def fetch_user_channel(request, code: str) -> ChannelInfo:
    async with Aiogoogle() as aiogoogle:
        full_user_creds = await aiogoogle.oauth2.build_user_creds(
            grant=code,
            client_creds=dict(
                redirect_uri=request.url_for('auth_google'),
                **settings.get().youtube.oauth.dict(),
            ),
        )
    return await fetch_channel_by_owner(full_user_creds)
