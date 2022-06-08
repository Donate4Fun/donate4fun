import logging
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from hypercorn.asyncio import serve
from hypercorn.config import Config
from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette_authlib.middleware import AuthlibMiddleware

from .settings import load_settings, Settings
from .db import load_db
from .lnd import monitor_invoices_loop, LndClient
from . import api, web

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_app(settings: Settings):
    app = FastAPI(debug=settings.debug)
    if settings.debug:
        app.add_middleware(DebugToolbarMiddleware)
    app.add_middleware(AuthlibMiddleware, secret_key=settings.jwt_secret)
    app.mount("/static", StaticFiles(directory="donate4fun/static"), name="static")
    app.include_router(api.router, prefix="/api/v1")
    app.include_router(web.router, prefix="")
    yield app


async def main():
    async with load_settings() as settings, create_app() as app, load_db(settings.db) as db, anyio.create_task_group() as tg:
        lnd = LndClient(settings.lnd)
        await tg.start(monitor_invoices_loop, lnd, db)
        hyper_config = Config.from_mapping(settings.hypercorn)
        app.db = db
        app.lnd = lnd
        await serve(app, hyper_config)
        tg.cancel_scope.cancel()
