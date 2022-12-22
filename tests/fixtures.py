import asyncio
import uuid
import contextvars
import functools
import logging
import socket
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from base64 import urlsafe_b64encode
from itertools import count
from uuid import UUID

import anyio
import pytest
import ecdsa
import posthog
from asgi_testclient import TestClient
from sqlalchemy import update
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config

from donate4fun.core import as_task
from donate4fun.app import create_app
from donate4fun.api_utils import task_group
from donate4fun.models import Invoice, Donation
from donate4fun.lnd import LndClient, lnd as lnd_var
from donate4fun.settings import load_settings, Settings, DbSettings
from donate4fun.db import DbSession, Database, db as db_var
from donate4fun.db_models import DonatorDb
from donate4fun.models import (
    RequestHash, PaymentRequest, YoutubeChannel, Donator, YoutubeVideo, TwitterAccount, TwitterTweet,
)
from donate4fun.pubsub import PubSubBroker, pubsub as pubsub_var
from donate4fun.dev_helpers import get_carol_lnd, get_alice_lnd

from tests.test_util import login_to


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
    stack = traceback.extract_stack()
    for frame in stack[-2::-1]:
        package_name = Path(frame.filename).parts[-2]
        if package_name != 'asyncio':
            if package_name == 'pytest_asyncio':
                # This function was called from pytest_asyncio, use shared context
                break
            else:
                # This function was called from somewhere else, create context copy
                context = None
            break
    return Task311(coro, loop=loop, context=context)


@pytest.fixture(scope="session")
def event_loop():
    """
    This fixture is used by pytest-asyncio to run test's setup/run/teardown.
    It's needed to share contextvars between these stages.
    This breaks context isolation for tasks, so we need to check calling context there
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    context = contextvars.copy_context()
    loop.set_task_factory(functools.partial(task_factory, context=context))
    asyncio.set_event_loop(loop)
    return loop


@pytest.fixture
async def settings():
    with load_settings() as settings:
        settings.fastapi.debug = False  # We need to disable Debug Toolbar to avoid zero-division error (because of freezegun)
        settings.rollbar = None
        settings.bugsnag.enabled = False
        settings.posthog.enabled = False
        settings.twitter.bearer_token = None
        yield settings


@pytest.fixture
async def db(settings: Settings):
    async with create_db("donate4fun-test") as db:
        yield db


@asynccontextmanager
async def create_db(db_name: str):
    base_db = Database(DbSettings(url='postgresql+asyncpg://tester@localhost/postgres', isolation_level='AUTOCOMMIT'))
    await base_db.create_database(db_name)
    try:
        db = Database(DbSettings(url=f'postgresql+asyncpg://tester@localhost/{db_name}'))
        await db.create_tables()
        yield db
    finally:
        await db.dispose()  # Close connections to release test db
        await base_db.drop_database(db_name)


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


async def run(command):
    process = await anyio.run_process(command.split(), cwd='docker')
    assert process.returncode == 0


@pytest.fixture
async def pubsub(db):
    pubsub = PubSubBroker()
    async with pubsub.run(db):
        yield pubsub


@pytest.fixture
async def app(db, settings, pubsub):
    posthog.disabled = True
    async with create_app(settings) as app, anyio.create_task_group() as tg:
        lnd = get_alice_lnd()
        with db_var.assign(db), lnd_var.assign(lnd), pubsub_var.assign(pubsub), task_group.assign(tg):
            yield app


@pytest.fixture
def freeze_request_hash_json(monkeypatch):
    r_hash = urlsafe_b64encode(b'hash').decode()

    def mock_to_json(self):
        return r_hash
    monkeypatch.setattr(RequestHash, 'to_json', mock_to_json)
    return r_hash


@pytest.fixture
def freeze_request_hash(monkeypatch):
    def mockinit(self, _):
        self.data = b'hash'
    monkeypatch.setattr(RequestHash, '__init__', mockinit)


@pytest.fixture
def freeze_payment_request(monkeypatch):
    def mocknew(cls, value):
        return str.__new__(cls, f'{cls.prefixes[0]}something')
    monkeypatch.setattr(PaymentRequest, '__new__', mocknew)


@pytest.fixture
def freeze_uuids(monkeypatch):
    def make_gen():
        c = count(1)
        return lambda: UUID(int=next(c))
    for model in [Donation, YoutubeChannel, YoutubeVideo, TwitterAccount, TwitterTweet]:
        monkeypatch.setattr(model.__fields__['id'], 'default_factory', make_gen())


@pytest.fixture
async def unpaid_donation_fixture(app, db, donator_id, freeze_uuids, settings):
    async with db.session() as db_session:
        youtube_channel = YoutubeChannel(
            channel_id='q2dsaf', title='asdzxc', thumbnail_url='http://example.com/thumbnail',
        )
        await db_session.save_youtube_channel(youtube_channel)
        invoice: Invoice = await LndClient(settings.lnd).create_invoice(memo="Donate4.fun to asdzxc", value=100)
        donation: Donation = Donation(
            donator=Donator(id=donator_id),
            amount=20,
            youtube_channel=youtube_channel,
            r_hash=invoice.r_hash,
        )
        await db_session.create_donation(donation)
        return donation


@pytest.fixture
async def paid_donation_fixture(db, unpaid_donation_fixture) -> Donation:
    async with db.session() as db_session:
        await db_session.donation_paid(
            donation_id=unpaid_donation_fixture.id,
            amount=unpaid_donation_fixture.amount,
            paid_at=datetime.now(),
        )
        return await db_session.query_donation(id=unpaid_donation_fixture.id)


@pytest.fixture
async def client(app, donator_id, settings):
    client = TestClient(app)
    login_to(client, settings, Donator(id=donator_id))
    return client


@pytest.fixture
async def registered_donator(db):
    return await make_registered_donator(db, UUID(int=1))  # UUID should differ from donator_id fixture


async def make_registered_donator(db, donator_id: UUID):
    sk = ecdsa.SigningKey.generate(entropy=ecdsa.util.PRNG(donator_id.bytes), curve=ecdsa.SECP256k1)
    pubkey = sk.verifying_key.to_string().hex()
    async with db.session() as db_session:
        await db_session.login_donator(donator_id, key=pubkey)
        return await db_session.query_donator(donator_id)


@pytest.fixture
async def rich_donator(db, registered_donator):
    async with db.session() as db_session:
        await db_session.execute(
            update(DonatorDb)
            .values(balance=100)
            .where(DonatorDb.id == registered_donator.id)
        )
        return await db_session.query_donator(id=registered_donator.id)


@pytest.fixture
async def payer_lnd():
    return get_carol_lnd()


@pytest.fixture
async def twitter_account(app, db, freeze_uuids):
    async with db.session() as db_session:
        account = TwitterAccount(
            user_id=1572908920485576704,
            handle='donate4_fun',
            name='Donate4.Fun ⚡',
            profile_image_url='https://pbs.twimg.com/profile_images/1574697734535348224/dzdW0yfs_normal.png',
            last_fetched_at=datetime.utcnow(),
        )
        await db_session.save_twitter_account(account)
        return account


def find_unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(('localhost', 0))
        return sock.getsockname()[1]


@as_task
async def app_serve(app, port):
    hyper_config = Config()
    hyper_config.bind = f'localhost:{port}'
    await hypercorn_serve(app, hyper_config)
