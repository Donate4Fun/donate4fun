import logging

from sqlalchemy import func

from .db import db
from .models import TwitterAccount, YoutubeChannel
from .db_models import TwitterAuthorDb, YoutubeChannelDb
from .settings import settings
from .twitter import fetch_twitter_author
from .youtube import fetch_youtube_channel
from .core import register_command

logger = logging.getLogger(__name__)


@register_command
async def refetch_twitter_authors():
    async with db.session() as db_session:
        accounts: list[TwitterAccount] = await db_session.query_twitter_accounts(
            (TwitterAuthorDb.last_fetched_at < func.now() - settings.twitter.refresh_timeout)
            | TwitterAuthorDb.last_fetched_at.is_(None)
        )
    logger.info("refetching %d authors", len(accounts))
    for account in accounts:
        account: TwitterAccount = await fetch_twitter_author(user_id=account.user_id)
        async with db.session() as db_session:
            await db_session.save_twitter_account(account)


@register_command
async def refetch_youtube_channels():
    async with db.session() as db_session:
        channels: list[YoutubeChannel] = await db_session.query_youtube_channels(
            (YoutubeChannelDb.last_fetched_at < func.now() - settings.youtube.refresh_timeout)
            | YoutubeChannelDb.last_fetched_at.is_(None)
        )
    logger.info("refetching %d channels", len(channels))
    for channel in channels:
        channel: YoutubeChannel = await fetch_youtube_channel(channel_id=channel.channel_id)
        async with db.session() as db_session:
            await db_session.save_youtube_channel(channel)


@register_command
async def notify(topic: str, object_id: str):
    async with db.session() as db_session:
        await db_session.object_changed(topic, object_id)
