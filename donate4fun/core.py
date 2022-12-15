import io
import asyncio
import logging
from base64 import b64encode
from contextvars import ContextVar
from contextlib import contextmanager, asynccontextmanager
from functools import wraps

import qrcode
import httpx
from qrcode.image.pure import PymagingImage

from .types import PaymentRequest

logger = logging.getLogger(__name__)


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
            logger.exception("API exception in %s: %s", func.__name__, exc.response.content)
        except Exception:
            logger.exception("Exception in %s", func.__name__)

    return wrapper


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


addLoggingLevel('TRACE', 5, 'trace')
