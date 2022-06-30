from contextvars import ContextVar

import yaml
import pytest


# This file is needed because pytest modifies "assert" only in test_*.py files


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
async def fixture_test():
    token = var.set('asd')
    yield
    var.reset(token)


async def test_async_context(fixture_test):
    assert var.get() == 'asd'


def check_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, response.text
    return response


def verify_response(response, name, status_code=None):
    if status_code is not None:
        check_response(response, status_code)
    content_type = response.headers['content-type']
    if content_type == 'application/json':
        data = dict(status_code=response.status_code, json=response.json())
    elif content_type == 'application/xml':
        data = dict(status_code=response.status_code, xml=response.text)
    verify_fixture(data, name)
