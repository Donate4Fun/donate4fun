import logging

from sqlalchemy import func

from .db import db
from .models import TwitterAccount
from .db_models import TwitterAuthorDb
from .settings import settings
from .twitter import fetch_twitter_author
from .core import register_command

logger = logging.getLogger(__name__)


@register_command
async def refetch_twitter_authors():
    async with db.session() as db_session:
        accounts: list[TwitterAccount] = await db_session.query_twitter_accounts(
            TwitterAuthorDb.last_fetched_at < func.now() - settings.twitter.refresh_timeout,
        )
    logger.info("refetching %d authors", len(accounts))
    for account in accounts:
        account: TwitterAccount = await fetch_twitter_author(user_id=account.user_id)
        async with db.session() as db_session:
            await db_session.save_twitter_account(account)
