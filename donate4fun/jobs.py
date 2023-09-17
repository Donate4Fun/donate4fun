import logging

from sqlalchemy import func

from .db import db
from .models import TwitterAccount, YoutubeChannel
from .db_models import TwitterAuthorDb, YoutubeChannelDb
from .db_libs import TwitterDbLib, YoutubeDbLib
from .settings import settings
from .twitter import TwitterApiClient
from .youtube import fetch_youtube_channel
from .api_utils import register_app_command

logger = logging.getLogger(__name__)


@register_app_command
async def refetch_twitter_authors():
    async with db.session() as db_session:
        accounts: list[TwitterAccount] = await TwitterDbLib(db_session).query_accounts(
            (TwitterAuthorDb.last_fetched_at < func.now() - settings.twitter.refresh_timeout)
            | TwitterAuthorDb.last_fetched_at.is_(None)
        )
    logger.info("refetching %d authors", len(accounts))
    async with TwitterApiClient.create_apponly(token=settings.twitter.linking_oauth.bearer_token) as client:
        for account in accounts:
            try:
                account: TwitterAccount = await client.get_user_by(user_id=account.user_id)
            except Exception:
                logger.exception("Failed to fetch twitter account %s", account)
            else:
                async with db.session() as db_session:
                    await TwitterDbLib(db_session).save_account(account)


@register_app_command
async def refetch_youtube_channels():
    async with db.session() as db_session:
        channels: list[YoutubeChannel] = await YoutubeDbLib(db_session).query_accounts(
            (YoutubeChannelDb.last_fetched_at < func.now() - settings.youtube.refresh_timeout)
            | YoutubeChannelDb.last_fetched_at.is_(None)
        )
    logger.info("refetching %d channels", len(channels))
    for channel in channels:
        try:
            channel: YoutubeChannel = await fetch_youtube_channel(channel_id=channel.channel_id)
        except Exception:
            logger.exception("Failed to fetch youtube channel %s", channel)
        else:
            async with db.session() as db_session:
                await YoutubeDbLib(db_session).save_account(channel)


@register_app_command
async def notify(topic: str, object_id: str):
    async with db.session() as db_session:
        await db_session.object_changed(topic, object_id)
