from contextvars import ContextVar
from contextlib import asynccontextmanager
from uuid import UUID

import anyio
import pytest
import yaml
from vcr.filters import replace_query_parameters

from donate4fun.models import Donator
from donate4fun.db import Notification
from tests.fixtures import Session, Settings


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


freeze_time = pytest.mark.freeze_time('2022-02-02 22:22:22', ignore=['logging'])


@asynccontextmanager
async def check_notification(client, topic: str, id_: UUID):
    async with client.ws_session(f"/api/v1/subscribe/{topic}:{id_}") as ws:
        yield
        with anyio.fail_after(5):
            notification = Notification.parse_obj(await ws.receive_json())
        assert notification.status == 'OK'


def login_to(client, settings: Settings, donator: Donator):
    # Relogin to rich donator (with balance > 0)
    client.cookies = dict(session=Session(donator=donator.id, jwt_secret=settings.jwt_secret).to_jwt())


def remove_credentials_and_testclient(request):
    if 'grpc-metadata-macaroon' in request.headers:
        del request.headers['grpc-metadata-macaroon']
    if request.host == 'youtube.googleapis.com':
        # WORKAROUND: key is a private credential
        replace_query_parameters(request, [('key', None)])
    if request.host == 'test':
        # Ignore testclient requests
        return None
    if request.host.startswith('localhost'):
        # Ignore requests to lnd
        return None
    return request


def remove_url(response):
    # WORKAROUND: this is a fix for vcrpy async handler
    if 'url' in response:
        response['url'] = ''
    return response


mark_vcr = pytest.mark.vcr(before_record_request=remove_credentials_and_testclient, before_record_response=remove_url)
