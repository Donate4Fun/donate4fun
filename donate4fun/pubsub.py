import asyncio
import logging
from functools import partial
from typing import Callable
from contextlib import asynccontextmanager

from .db import Database

logger = logging.getLogger(__name__)


async def callback_wrapper(callback: Callable, conn, pid, channel, payload: str):
    try:
        if asyncio.iscoroutinefunction(callback):
            return await callback(payload)
        else:
            return callback(payload)
    except Exception:
        logger.exception(f"Unhandled exception in pubsub callback while processing '{channel}' {payload}")
        raise


class PubSubBroker:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.asyncpg_connection = None

    def __str__(self):
        return f'{type(self).__name__}<{hex(id(self))}>'

    @asynccontextmanager
    async def subscribe(self, channel: str, callback: Callable):
        wrapped_callback = partial(callback_wrapper, callback)
        async with self.lock, self.asyncpg_connection.transaction():
            await self.asyncpg_connection.add_listener(channel, wrapped_callback)
        logger.debug(f"Subscribed to '{channel}'")
        try:
            yield
        except Exception:
            logger.exception("exception in subscribe yield")
        finally:
            logger.debug(f"Unsubscribing from '{channel}'")
            try:
                async with self.lock, self.asyncpg_connection.transaction():
                    await self.asyncpg_connection.remove_listener(channel, wrapped_callback)
            except asyncio.CancelledError:
                logger.exception("exception in remove listener")
                raise

    @asynccontextmanager
    async def run(self, db: Database):
        async with db.raw_session() as session:
            connection = await session.connection(execution_options=dict(logging_token=str(self)))
            raw_connection = await connection.get_raw_connection()
            self.asyncpg_connection = raw_connection.connection._connection
            yield
