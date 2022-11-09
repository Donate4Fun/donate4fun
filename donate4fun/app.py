import logging
import sys
import os
from contextlib import asynccontextmanager

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
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError
from pydantic import ValidationError as PydanticValidationError

from .settings import load_settings, Settings, settings
from .db import Database, NoResultFound
from .lnd import monitor_invoices, LndClient
from .pubsub import PubSubBroker
from .types import ValidationError
from . import api, web

logger = logging.getLogger(__name__)


def http_status_error_handler(request, exc):
    logger.debug(f"{request.url}: Upstream error", exc_info=exc)
    status_code = exc.response.status_code
    body = exc.response.json()
    return JSONResponse(status_code=500, content={"message": f"Upstream server returned {status_code}: {body}"})


def no_result_found_handler(request, exc):
    return JSONResponse(status_code=404, content=dict(message="Item not found"))


def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=dict(
            status="error",
            type=type(exc).__name__,
            error=str(exc),
        ),
    )


def pydantic_validation_error_handler(request, exc):
    logger.debug(f"{request.url}: Validation error", exc_info=exc)
    return JSONResponse(
        status_code=400,
        content=dict(
            status="error",
            type=type(exc).__name__,
            error=exc.errors()[0]['msg'],
        ),
    )


@asynccontextmanager
async def create_app(settings: Settings):
    origins = [
        "https://youtube.com",
        "https://www.youtube.com",
        "https://m/youtube.com",
    ]

    app = FastAPI(
        debug=settings.fastapi.debug,
        root_path=settings.fastapi.root_path,
        exception_handlers={
            HTTPStatusError: http_status_error_handler,
            NoResultFound: no_result_found_handler,
            ValidationError: validation_error_handler,
            PydanticValidationError: pydantic_validation_error_handler,
        },
    )
    if settings.rollbar:
        rollbar.init(**settings.rollbar.dict())
    if settings.fastapi.debug:
        app.add_middleware(
            DebugToolbarMiddleware,
            panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
            profiler_options=dict(interval=.0002, async_mode='enabled'),
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    # same_site = None is needed for CORS auth
    app.add_middleware(
        AuthMiddleware, settings=settings,
        domain=settings.cookie_domain,
    )
    app.add_middleware(ServerNameMiddleware)
    app.mount("/static", StaticFiles(directory="donate4fun/static"), name="static")
    app.include_router(api.router, prefix="/api/v1")
    app.include_router(web.router, prefix="")
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
        super().__init__(**kwargs, secret_key=settings.jwt_secret, same_site="None", https_only=settings.cookie_https_only)
        if not settings.cookie_http_only:
            self.security_flags = self.security_flags.replace('httponly; ', '')


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    commands = dict(
        serve=serve,
        createdb=create_db,
        createtable=create_table,
    )
    await commands[command](*sys.argv[2:])


async def create_db():
    with load_settings() as settings:
        db = Database(settings.db)
        await db.create_tables()


async def create_table(tablename: str):
    with load_settings() as settings:
        db = Database(settings.db)
        await db.create_table(tablename)


async def serve():
    addLoggingLevel('TRACE', 5, 'trace')
    with load_settings() as settings:
        async with create_app(settings) as app:
            if settings.bugsnag.enabled:
                bugsnag.configure(**settings.bugsnag.dict(), project_root=os.path.dirname(__file__))
            lnd = LndClient(settings.lnd)
            db = Database(settings.db)
            pubsub = PubSubBroker()
            app.db = db
            app.lnd = lnd
            app.pubsub = pubsub
            async with pubsub.run(db), monitor_invoices(lnd, db), anyio.create_task_group() as tg:
                app.task_group = tg
                hyper_config = Config.from_mapping(settings.hypercorn)
                hyper_config.accesslog = logging.getLogger('hypercorn.acceslog')
                await hypercorn_serve(BugsnagMiddleware(app), hyper_config)


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
