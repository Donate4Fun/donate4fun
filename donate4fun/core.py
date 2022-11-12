import io
import asyncio
import logging
from base64 import b64encode
from contextvars import ContextVar
from contextlib import contextmanager, asynccontextmanager
from functools import wraps

import qrcode
import httpx
from fastapi import Request, WebSocket
from qrcode.image.pure import PymagingImage

from .types import PaymentRequest

logger = logging.getLogger(__name__)


async def get_db_session(request: Request):
    async with request.app.db.session() as session:
        yield session


async def get_db(request: Request):
    return request.app.db


async def get_lnd(request: Request):
    return request.app.lnd


async def get_pubsub(websocket: WebSocket):
    return websocket.app.pubsub


def payreq_to_datauri(pay_req: PaymentRequest):
    """
    converts ln payment request to qr code in form of data: uri
    """
    img = qrcode.make(pay_req, image_factory=PymagingImage)
    data = io.BytesIO()
    img.save(data)
    return to_datauri('image/png', data.getvalue())


def to_datauri(mime_type: str, data: bytes) -> str:
    encoded = b64encode(data).decode()
    return f'data:{mime_type};base64,{encoded}'


class ContextualObject:
    def __init__(self, name: str):
        self.__dict__['var'] = ContextVar(name)

    @contextmanager
    def assign(self, var):
        token = self.__dict__['var'].set(var)
        try:
            yield self
        finally:
            self.var.reset(token)

    def __getattr__(self, attrname):
        return getattr(self.__dict__['var'].get(), attrname)

    def __setattr__(self, attrname, value):
        return setattr(self.__dict__['var'].get(), attrname, value)

    def __call__(self, *args, **kwargs):
        return self.__dict__['var'].get().__call__(*args, **kwargs)


async def log_exception(coro):
    try:
        return await coro
    except httpx.HTTPStatusError as exc:
        logger.exception(
            "Unhandled HTTPStatusError. Response: %s. Request: %s (%s)",
            exc.response.json(), exc.request.headers, exc.request.content,
        )
        raise
    except Exception:
        logger.exception("Unhandled exception in %s", coro)
        raise


def as_task(func):
    @asynccontextmanager
    @wraps(func)
    async def manager(*args, **kwargs):
        task = asyncio.create_task(log_exception(func(*args, **kwargs)))
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    return manager


app = ContextualObject("app")
commands = {}


def register_command(func):
    commands[func.__name__] = func
    return func


def catch_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as exc:
            breakpoint()
            logger.exception("API exception in %s: %s", func.__name__, exc.response.content)
        except Exception:
            logger.exception("Exception in %s", func.__name__)

    return wrapper
