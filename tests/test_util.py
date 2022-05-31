from contextvars import ContextVar

import yaml
import pytest


def pytest_assert(left, right, message):
    assert left == right, message


def verify_fixture(data: bytes, name: str):
    filename = f'tests/autofixtures/{name}.yaml'
    try:
        with open(filename) as f:
            original = yaml.unsafe_load(f)
        assert original == data, f"Response for {filename} differs"
    except FileNotFoundError:
        with open(filename, 'w') as f:
            yaml.dump(data, f)


var = ContextVar('var')


@pytest.fixture
async def fixture_test(event_loop):
    token = var.set('asd')
    yield
    var.reset(token)


async def test_async_context(fixture_test):
    assert var.get() == 'asd'


def test_context(event_loop, fixture_test):
    var = ContextVar('var')

    async def afun_get():
        assert var.get() == 'asd'

    async def afun_reset(token):
        assert var.get() == 'asd'
        var.reset(token)

    async def afun_set():
        return var.set('asd')

    token = event_loop.run_until_complete(afun_set())
    event_loop.run_until_complete(afun_reset(token))
