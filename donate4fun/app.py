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
from .lnd import monitor_invoices
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
    with load_settings() as settings:
        async with create_app() as app, load_db() as db, anyio.create_task_group() as tg:
            tg.start_soon(monitor_invoices, db)
            hyper_config = Config.from_mapping(settings().hypercorn)
            app.db = db
            await serve(app, hyper_config)
            tg.cancel_scope.cancel()
