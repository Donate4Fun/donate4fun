import asyncio
import contextvars
import functools
import pytest

from donate4fun.app import create_app
from donate4fun.settings import load_settings
from donate4fun.db import load_db, DbSession
from donate4fun.lnd import query_state


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


class Task311(asyncio.tasks._PyTask):
    def __init__(self, coro, *, loop=None, name=None, context=None):
        super(asyncio.tasks._PyTask, self).__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]
        if not asyncio.coroutines.iscoroutine(coro):
            # raise after Future.__init__(), attrs are required for __del__
            # prevent logging for pending task in __del__
            self._log_destroy_pending = False
            raise TypeError(f"a coroutine was expected, got {coro!r}")

        if name is None:
            self._name = f'Task-{asyncio.tasks._task_name_counter()}'
        else:
            self._name = str(name)

        self._num_cancels_requested = 0
        self._must_cancel = False
        self._fut_waiter = None
        self._coro = coro
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context

        self._loop.call_soon(self._Task__step, context=self._context)
        asyncio.tasks._register_task(self)


def task_factory(loop, coro, context=None):
    return Task311(coro, loop=loop, context=context)


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for entire session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    context = contextvars.copy_context()
    loop.set_task_factory(functools.partial(task_factory, context=context))
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope='session')
async def settings():
    with load_settings() as settings:
        yield settings


@pytest.fixture(scope='session')
async def db(settings):
    async with load_db() as db:
        yield db


@pytest.fixture(scope="session")
async def app(db, settings):
    async with create_app(settings) as app:
        app.db = db
        yield app


@pytest.fixture()
async def lnd(settings):
    state = await query_state()
    assert state == 'SERVER_ACTIVE'


@pytest.fixture
async def db_session(db) -> DbSession:
    async with db.rollback() as session:
        yield session
