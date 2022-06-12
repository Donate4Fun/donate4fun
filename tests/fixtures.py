import asyncio
import uuid
import contextvars
import functools
import logging
from datetime import datetime

import anyio
import pytest

from donate4fun.app import create_app
from donate4fun.settings import load_settings, Settings, DbSettings
from donate4fun.db import DbSession, Database
from donate4fun.lnd import LndClient
from donate4fun.models import Donation


logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


class Task311(asyncio.tasks._PyTask):
    """
    This is backport of Task from CPython 3.11
    It's needed to allow context passing
    """
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
def event_loop():
    """Create an instance of the default event loop for entire session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    context = contextvars.copy_context()
    loop.set_task_factory(functools.partial(task_factory, context=context))
    yield loop
    loop.close()


@pytest.fixture
async def settings():
    async with load_settings() as settings:
        settings.lnd.url = 'http://localhost:10001'
        settings.lnd.macaroon_by_network = None
        settings.debug = False  # We need to disable Debug Toolbar to avoid zero-division error (because of freezegun)
        yield settings


@pytest.fixture
async def db(settings: Settings):
    base_db = Database(DbSettings(dsn='postgresql+asyncpg://tester@localhost/postgres', isolation_level='AUTOCOMMIT'))
    db_name = "donate4fun-test"
    await base_db.create_database(db_name)
    try:
        db = Database(DbSettings(dsn=f'postgresql+asyncpg://tester@localhost/{db_name}'))
        await db.create_tables()
        yield db
    finally:
        await db.dispose()  # Close connections to release test db
        await base_db.drop_database(db_name)


async def run(command):
    process = await anyio.run_process(command.split(), cwd='docker')
    assert process.returncode == 0


@pytest.fixture(scope="session")
async def lnd_server(event_loop):
    await run('docker-compose up -d')
    await run('bitcoin-cli -regtest -datadir=./bitcoind-data -generate 5')
    yield


@pytest.fixture
async def app(db, settings, lnd_server):
    async with create_app(settings) as app:
        app.db = db
        app.lnd = LndClient(settings.lnd)
        yield app


@pytest.fixture
async def db_session(db) -> DbSession:
    async with db.session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def freeze_uuid(monkeypatch):
    value = uuid.UUID(int=1)
    monkeypatch.setattr(uuid, 'uuid4', lambda: value)
    return value


@pytest.fixture
def donator_id():
    return uuid.UUID(int=0)


@pytest.fixture
async def donation_fixture(db, donator_id, freeze_uuid):
    async with db.session() as db_session:
        youtube_channel_id = await db_session.get_or_create_youtube_channel(
            channel_id='q2dsaf', title='asdzxc', thumbnail_url='1wdasd',
        )
        donation: Donation = await db_session.create_donation(
            donator_id=donator_id,
            amount=20,
            youtube_channel_id=youtube_channel_id,
            r_hash='hash',
        )
        return donation


@pytest.fixture
async def paid_donation_fixture(db, donation_fixture):
    async with db.session() as db_session:
        await db_session.donation_paid(r_hash=donation_fixture.r_hash, amount=donation_fixture.amount, paid_at=datetime.now())
