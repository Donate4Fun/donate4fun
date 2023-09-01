import asyncio
import uuid
import contextvars
import functools
import logging
import socket
import traceback
import os
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from base64 import urlsafe_b64encode
from itertools import count
from uuid import UUID

import anyio
import pytest
import ecdsa
from asgi_testclient import TestClient
from sqlalchemy import update
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from furl import furl

from donate4fun.core import as_task
from donate4fun.app import create_app, app as app_var, init_posthog
from donate4fun.api_utils import task_group
from donate4fun.lnd import LndClient, lnd as lnd_var
from donate4fun.settings import load_settings, Settings, DbSettings
from donate4fun.twitter import api_data_to_twitter_account
from donate4fun.db import DbSession, Database, db as db_var
from donate4fun.db_models import DonatorDb
from donate4fun.db_youtube import YoutubeDbLib
from donate4fun.db_twitter import TwitterDbLib
from donate4fun.db_donations import DonationsDbLib
from donate4fun.models import (
    Invoice, Donation, OAuthState, IdModel,
    RequestHash, PaymentRequest, YoutubeChannel, Donator, TwitterAccount,
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
async def settings(monkeypatch):
    monkeypatch.setattr('donate4fun.settings.default_settings_file', lambda: 'config-test.yaml')
    with load_settings() as settings:
        settings.fastapi.debug = False  # We need to disable Debug Toolbar to avoid zero-division error (because of freezegun)
        settings.rollbar = None
        settings.bugsnag = None
        settings.sentry = None
        settings.base_url = 'http://localhost:3000'
        settings.frontend_port = 3000
        init_posthog()
        yield settings


@pytest.fixture
def time_of_freeze():
    return datetime.fromisoformat('2022-02-02T22:22:22')


@pytest.fixture
async def freeze_last_fetched_at(monkeypatch, time_of_freeze):
    def patched_api_data_to_twitter_account(data: dict):
        account = api_data_to_twitter_account(data)
        account.last_fetched_at = time_of_freeze
        return account
    monkeypatch.setattr('donate4fun.twitter.api_data_to_twitter_account', patched_api_data_to_twitter_account)


@pytest.fixture
async def db(settings: Settings):
    async with create_db("donate4fun-test") as db:
        with db_var.assign(db):
            yield db


@asynccontextmanager
async def create_db(db_name: str):
    test_db_url = os.getenv('DONATE4FUN_TEST_DB_URL', 'postgresql+asyncpg://tester@localhost/postgres')
    base_db = Database(DbSettings(url=test_db_url, isolation_level='AUTOCOMMIT'))
    await base_db.create_database(db_name)
    db = Database(DbSettings(url=str(furl(test_db_url).set(path=db_name))))
    try:
        await db.create_tables()
        yield db
    finally:
        await db.dispose()  # Close connections to release test db
        await base_db.drop_database(db_name)
        await base_db.dispose()


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
    async with create_app(settings) as app, anyio.create_task_group() as tg:
        lnd = get_alice_lnd()
        with app_var.assign(app), lnd_var.assign(lnd), pubsub_var.assign(pubsub), task_group.assign(tg):
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


def all_subclasses(cls):
    return {cls}.union(
        s for c in cls.__subclasses__() for s in all_subclasses(c)
    ) if cls.__module__.startswith('donate4fun') else set()


@pytest.fixture
def freeze_uuids(monkeypatch):
    def make_gen():
        c = count(1)
        return lambda: UUID(int=next(c))
    for model in all_subclasses(IdModel):
        monkeypatch.setattr(model.__fields__['id'], 'default_factory', make_gen())


@pytest.fixture
async def unpaid_donation_fixture(app, db, donator_id, freeze_uuids, settings):
    async with db.session() as db_session:
        youtube_db = YoutubeDbLib(db_session)
        youtube_channel = YoutubeChannel(
            channel_id='q2dsaf', title='asdzxc', thumbnail_url='http://example.com/thumbnail',
        )
        await youtube_db.save_account(youtube_channel)
        invoice: Invoice = await LndClient(settings.lnd).create_invoice(memo="Donate4.fun to asdzxc", value=100)
        donation: Donation = Donation(
            donator=Donator(id=donator_id),
            amount=20,
            youtube_channel=youtube_channel,
            r_hash=invoice.r_hash,
        )
        await DonationsDbLib(db_session).create_donation(donation)
        return donation


@pytest.fixture
async def paid_donation_fixture(db, unpaid_donation_fixture) -> Donation:
    async with db.session() as db_session:
        donations_db = DonationsDbLib(db_session)
        await donations_db.donation_paid(
            donation_id=unpaid_donation_fixture.id,
            amount=unpaid_donation_fixture.amount,
            paid_at=datetime.now(),
        )
        return await donations_db.query_donation(id=unpaid_donation_fixture.id)


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
async def twitter_account(app, db, freeze_uuids, time_of_freeze):
    async with db.session() as db_session:
        account = TwitterAccount(
            user_id=1572908920485576704,
            handle='donate4_fun',
            name='Donate4.Fun ⚡',
            profile_image_url='https://pbs.twimg.com/profile_images/1574697734535348224/dzdW0yfs_normal.png',
            last_fetched_at=time_of_freeze,
        )
        await TwitterDbLib(db_session).save_account(account)
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


@pytest.fixture
async def twitter_db(db_session):
    return TwitterDbLib(db_session)


@pytest.fixture
async def youtube_db(db_session):
    return YoutubeDbLib(db_session)


@pytest.fixture
def oauth_state():
    return OAuthState(success_path='/success', error_path='/error', donator_id=UUID(int=0), code_verifier=b'\x00' * 43)
