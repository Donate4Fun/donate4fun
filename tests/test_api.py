from uuid import UUID

import anyio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from vcr.filters import replace_query_parameters
from asgi_testclient import TestClient

from donate4fun.api import DonateRequest
from donate4fun.models import Donation
from donate4fun.lnd import monitor_invoices
from tests.test_util import verify_fixture
from tests.fixtures import *  # noqa

#pytestmark = pytest.mark.anyio


@pytest.fixture
async def client(app, lnd):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


#@pytest.fixture
@pytest_asyncio.fixture
async def ah_client(app, lnd, aiohttp_client):
    return await aiohttp_client(app)


@pytest.fixture
async def fastapi_client(app):
    return TestClient(app)


@pytest.fixture
def asgi_client(app):
    return TestClient(app)


@pytest.fixture
async def donation_fixture(db_session):
    youtube_channel_id = await db_session.get_or_create_youtube_channel(
        channel_id='q2dsaf', title='asdzxc', thumbnail_url='1wdasd',
    )
    donation: Donation = await db_session.create_donation(
        donator_id=UUID('9842425d-f653-4758-9afc-40a576561597'),
        amount=20,
        youtube_channel_id=youtube_channel_id,
        r_hash='hash',
    )
    return donation


def check_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, response.text
    return response


def verify_response(response, name, status_code=None):
    if status_code is not None:
        check_response(response, status_code)
    data = dict(status_code=response.status_code, json=response.json())
    verify_fixture(data, name)


async def test_latest_donations(client):
    response = await client.get("/api/v1/latest-donations")
    verify_response(response, 'latest-donations', 200)


async def test_create_donation_unsupported_target(client):
    response = await client.post("/api/v1/donate", json=DonateRequest(amount=100, target='https://asdzxc.com').dict())
    verify_response(response, 'create-donation-unsupported_target', 400)


async def test_create_donation_unsupported_youtube_url(client):
    response = await client.post("/api/v1/donate", json=DonateRequest(amount=100, target='https://youtube.com/azxcasd').dict())
    verify_response(response, 'create-donation-unsupported_youtube_url', 400)


def remove_credentials_and_testclient(request):
    if 'grpc-metadata-macaroon' in request.headers:
        del request.headers['grpc-metadata-macaroon']
    if request.host == 'youtube.googleapis.com':
        replace_query_parameters(request, [('key', None)])
    if request.host == 'test':
        return None
    return request


def remove_url(response):
    if 'url' in response:
        response['url'] = ''
    return response


mark_vcr = pytest.mark.vcr(before_record_request=remove_credentials_and_testclient, before_record_response=remove_url)


@mark_vcr
async def test_create_donation(client, db):
    async with db.rollback():
        donate_response = await client.post(
            "/api/v1/donate",
            json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
        )
        verify_response(donate_response, 'create-donation', 200)


async def test_get_donation(asgi_client, donation_fixture):
    donation_response = await asgi_client.get(f"/api/v1/donation/{donation_fixture.id}")
    verify_response(donation_response, 'get-donation')


#@mark_vcr
@pytest.mark.asyncio
@pytest.mark.freeze_time('2022-05-31T12:54:19')
async def test_payment(asgi_client, db, db_session):
    donate_response = await asgi_client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    #verify_response(donate_response, 'payment-donate')
    donation_id = donate_response.json()['id']
    async with anyio.create_task_group() as tg, asgi_client.ws_session(f"/api/v1/donation/subscribe/{donation_id}") as ws:
        tg.start_soon(monitor_invoices, db)
        ws_response = []
        while True:
            resp = await ws.receive_json()
            print(resp)
            ws_response.append(resp)
        verify_fixture(ws_response, "payment-subscribe")
    donation_response = await asgi_client.get(f"/api/v1/donation/{donation_id}")
    verify_response(donation_response, "payment-donation")


async def test_websocket(asgi_client, donation_fixture):
    messages = []
    async with asgi_client.ws_session(f'/api/v1/donation/subscribe/{donation_fixture.id}') as ws:
        while True:
            messages.append(await ws.receive_json())
    assert messages == ''
