import logging

import httpx

from .settings import settings
from .db import db
from .twitter import TwitterApiClient
from .models import TwitterAccount
from .api_utils import register_app_command

logger = logging.getLogger(__name__)


@register_app_command
async def fetch_and_save_twitter_account(handle: str):
    token = settings.twitter.linking_oauth.bearer_token
    async with db.session() as db_session, TwitterApiClient.create_apponly(token=token) as client:
        account: TwitterAccount = await TwitterApiClient(client).get_user_by(handle=handle)
        await db_session.save_twitter_account(account)


@register_app_command
async def get_profile_banner():
    """
    Does it work?
    """
    async with db.session() as db_session:
        token: dict = await db_session.query_oauth_token('twitter_oauth1')
    async with TwitterApiClient.create_oauth1(token=token) as client:
        try:
            data: dict = await client.get_profile_branner(screen_name='elonmusk')
        except httpx.HTTPStatusError as exc:
            auth_header = exc.request.headers['authorization']
            logger.exception("Failed to get banner image:\n%s\n%s\n%s", auth_header, exc.request.headers, exc.response.json())
        else:
            print(data)
