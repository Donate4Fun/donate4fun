import json
from urllib.parse import parse_qs
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ClientCreds, ServiceAccountCreds
from .settings import settings
from .models import UnsupportedDonatee

ChannelId = str


class UnsupportedYoutubeUrl(UnsupportedDonatee):
    pass


async def validate_youtube_url(parsed):
    parts = parsed.path.split('/')
    if parsed.path == '/watch':
        video_id = parse_qs(parsed.query)['v']
        channel_id = await get_video_channel(video_id)
    elif parts[1] == 'channel':
        channel_id = parts[2]
    elif parsed.hostname == 'youtu.be':
        channel_id = parsed.path[1:]
    else:
        raise UnsupportedYoutubeUrl
    return make_youtube_channel_url(channel_id)


def make_youtube_channel_url(channel_id: str):
    return f'https://youtube.com/channel/{channel_id}'


async def get_user_channel(creds: ClientCreds) -> ChannelId:
    async with Aiogoogle(user_creds=creds) as aiogoogle:
        youtube_v3 = await aiogoogle.discover("youtube", "v3")
        req = youtube_v3.channels.list(mine=True, part='id')
        res = await aiogoogle.as_user(req)
        return res['items'][0]['id']


def get_service_account_creds():
    return ServiceAccountCreds(
        scopes=[
            "https://www.googleapis.com/auth/youtube.read_only",
        ],
        **json.load(open(settings().youtube.service_account_key_file))
    )


async def get_video_channel(video_id: str) -> ChannelId:
    async with Aiogoogle(service_account_creds=get_service_account_creds()) as aiogoogle:
        youtube_v3 = await aiogoogle.discover("youtube", "v3")
        req = youtube_v3.videos.list(id=video_id)
        res = await aiogoogle.as_service_account(req, part='snippet')
        return res['items'][0]['snippet']['channelId']
