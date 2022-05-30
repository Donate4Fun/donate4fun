import pytest

from donate4fun.app import create_app
from donate4fun.settings import load_settings
from donate4fun.db import load_db
from donate4fun.lnd import query_state


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(autouse=True, scope='session')
def settings():
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
