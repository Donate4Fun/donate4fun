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
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError
from pydantic import ValidationError as PydanticValidationError

from .settings import load_settings, Settings
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
        app.add_middleware(DebugToolbarMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    # same_site = None is needed for CORS auth
    app.add_middleware(
        AuthlibMiddleware, secret_key=settings.jwt_secret, same_site="None", https_only=settings.cookie_https_only,
        domain=settings.cookie_domain,
    )
    app.mount("/static", StaticFiles(directory="donate4fun/static"), name="static")
    app.include_router(api.router, prefix="/api/v1")
    app.include_router(web.router, prefix="")
    yield app


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    commands = dict(
        serve=serve,
        createdb=create_db,
    )
    await commands[command]()


async def create_db():
    async with load_settings() as settings:
        db = Database(settings.db)
        await db.create_tables()


async def serve():
    async with load_settings() as settings, create_app(settings) as app:
        if settings.bugsnag:
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
