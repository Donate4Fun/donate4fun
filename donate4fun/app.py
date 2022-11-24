import logging
import sys
import os
from contextlib import asynccontextmanager, AsyncExitStack

import anyio
import bugsnag
import rollbar
from bugsnag.asgi import BugsnagMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette_authlib.middleware import AuthlibMiddleware
from starlette.datastructures import MutableHeaders

from .settings import load_settings, Settings, settings
from .db import Database, db
from .lnd import monitor_invoices, LndClient, lnd
from .pubsub import PubSubBroker, pubsub
from .twitter import run_twitter_bot_restarting
from .core import app, register_command, commands
from .screenshot import create_screenshoter_app
from .api_utils import task_group
from . import api, web

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_app(settings: Settings):
    app = FastAPI(
        debug=settings.fastapi.debug,
        root_path=settings.fastapi.root_path,
    )
    if settings.rollbar:
        rollbar.init(**settings.rollbar.dict())
    if settings.fastapi.debug:
        api.app.add_middleware(
            DebugToolbarMiddleware,
            panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
            profiler_options=dict(interval=.0002, async_mode='enabled'),
        )
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
    # same_site = None is needed for CORS auth
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
        super().__init__(**kwargs, secret_key=settings.jwt_secret, same_site="None", https_only=settings.cookie_secure)
        if not settings.cookie_http_only:
            self.security_flags = self.security_flags.replace('httponly; ', '')


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    addLoggingLevel('TRACE', 5, 'trace')
    with load_settings(), db.assign(Database(settings.db)):
        result = await commands[command](*sys.argv[2:])
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
    await db.create_tables()


@register_command
async def create_table(tablename: str):
    await db.create_table(tablename)


@register_command
async def serve():
    pubsub_ = PubSubBroker()
    lnd_ = LndClient(settings.lnd)
    async with create_app(settings) as app_, anyio.create_task_group() as tg:
        if settings.bugsnag.enabled:
            bugsnag.configure(**settings.bugsnag.dict(), project_root=os.path.dirname(__file__))
        with app.assign(app_), lnd.assign(lnd_), pubsub.assign(pubsub_), task_group.assign(tg):
            async with pubsub.run(db), monitor_invoices(lnd_, db), AsyncExitStack() as stack:
                if settings.twitter.enable_bot:
                    await stack.enter_async_context(run_twitter_bot_restarting(db))
                hyper_config = Config.from_mapping(settings.hypercorn)
                hyper_config.accesslog = logging.getLogger('hypercorn.acceslog')
                if settings.bugsnag.enabled:
                    app_ = BugsnagMiddleware(app_)
                await hypercorn_serve(app_, hyper_config)


# https://stackoverflow.com/a/35804945/1022684
def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)
