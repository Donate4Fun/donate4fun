import logging
import sys
import os
from contextlib import asynccontextmanager

import anyio
import bugsnag
from bugsnag.asgi import BugsnagMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette_authlib.middleware import AuthlibMiddleware

from .settings import load_settings, Settings
from .db import Database
from .lnd import monitor_invoices_loop, LndClient
from . import api, web

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_app(settings: Settings):
    origins = [
        "https://youtube.com",
        "https://www.youtube.com",
        "https://m/youtube.com",
    ]

    app = FastAPI(debug=settings.fastapi.debug, root_path=settings.fastapi.root_path)
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
    app.add_middleware(AuthlibMiddleware, secret_key=settings.jwt_secret, same_site="None")
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
    async with load_settings() as settings, create_app(settings) as app, anyio.create_task_group() as tg:
        if settings.bugsnag.api_key:
            bugsnag.configure(**settings.bugsnag.dict(), project_root=os.path.dirname(__file__))
        lnd = LndClient(settings.lnd)
        db = Database(settings.db)
        hyper_config = Config.from_mapping(settings.hypercorn)
        app.db = db
        app.lnd = lnd
        app.task_group = tg
        tg.start_soon(monitor_invoices_loop, lnd, db)
        await hypercorn_serve(BugsnagMiddleware(app), hyper_config)
        tg.cancel_scope.cancel()
