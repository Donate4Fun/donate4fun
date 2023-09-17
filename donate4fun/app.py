import asyncio
import logging
import sys
from contextlib import asynccontextmanager, AsyncExitStack

import anyio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette_authlib.middleware import AuthlibMiddleware
from starlette.datastructures import MutableHeaders
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from .settings import load_settings, Settings, settings
from .db import Database, db
from .lnd import monitor_invoices, LndClient, lnd
from .pubsub import create_pubsub
from . import twitter_bot
from .core import app, register_command, commands
from .screenshot import create_screenshoter_app
from .api_utils import task_group, with_common_libs
from . import api, web

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_app():
    app = FastAPI(
        debug=settings.fastapi.debug,
        root_path=settings.fastapi.root_path,
    )
    if settings.fastapi.debug:
        api.app.add_middleware(
            DebugToolbarMiddleware,
            panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
            profiler_options=dict(interval=.0002, async_mode='enabled'),
        )
    if settings.sentry:
        app.add_middleware(SentryAsgiMiddleware)

    api.app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            # YouTube connects directly from content script, so add it's origins
            "https://youtube.com",
            "https://www.youtube.com",
            "https://m.youtube.com",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    # `same_site = None` is needed for CORS auth
    api.app.add_middleware(
        AuthMiddleware, settings=settings,
        domain=settings.cookie_domain,
    )
    app.add_middleware(ServerNameMiddleware)
    app.mount("/static", StaticFiles(directory="frontend/public/static"), name="static")
    app.mount('/api/v1', api.app)
    async with create_screenshoter_app() as screenshoter_app:
        app.mount('/preview', screenshoter_app)
        app.mount('/', web.app)  # Should be mounted last
        yield app


class ServerNameMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_name(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers['Server'] = settings.server_name
            await send(message)

        await self.app(scope, receive, send_with_name)


class AuthMiddleware(AuthlibMiddleware):
    def __init__(self, settings: Settings, **kwargs):
        super().__init__(
            **kwargs,
            secret_key=settings.jwt_secret,
            same_site=settings.cookie_same_site,
            https_only=settings.cookie_secure,
        )
        if not settings.cookie_http_only:
            self.security_flags = self.security_flags.replace('httponly; ', '')


def cli():
    asyncio.run(main(sys.argv))


async def main(args):
    command = args[1] if len(args) > 1 else 'serve'
    if '.' in command:
        module, command = command.split('.')
        __import__(f'donate4fun.{module}')
    result = await commands[command](*args[2:])
    if result is not None:
        print(result)


@register_command
async def help():
    """Show this help"""
    print('Available commands:\n\n' + '\n'.join(
        f'{command}\t- {func.__doc__}' if func.__doc__ else command for command, func in commands.items()
    ))


@register_command
async def create_db():
    with load_settings(), db.assign(Database(settings.db)):
        await db.create_tables()


@register_command
async def create_table(tablename: str):
    with load_settings(), db.assign(Database(settings.db)):
        await db.create_table(tablename)


class AccessFilter(logging.Filter):
    """
    This filter removes /api/v1/status logs from accesslog
    """
    def filter(self, record):
        return record.args.get('U') != '/api/v1/status'


@register_command
@with_common_libs
async def serve():
    lnd_ = LndClient(settings.lnd)
    async with create_app() as app_, anyio.create_task_group() as tg:
        with app.assign(app_), lnd.assign(lnd_), task_group.assign(tg):
            async with create_pubsub(), monitor_invoices(lnd_, db), AsyncExitStack() as stack:
                if settings.twitter.conversations_bot.enabled:
                    await stack.enter_async_context(twitter_bot.run_converstaions_bot())
                if settings.twitter.mentions_bot.enabled:
                    await stack.enter_async_context(twitter_bot.run_mentions_bot())
                hyper_config = Config.from_mapping(settings.hypercorn)
                hyper_config.accesslog = logging.getLogger('hypercorn.accesslog')
                hyper_config.accesslog.addFilter(AccessFilter())
                iface = hyper_config.bind[0].split(':')[0]
                hyper_config.bind = f'{iface}:{settings.api_port}'
                await hypercorn_serve(app_, hyper_config)
