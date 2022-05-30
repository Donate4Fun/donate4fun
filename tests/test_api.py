import pytest
from httpx import AsyncClient
from vcr.filters import replace_query_parameters

from donate4fun.api import DonateRequest
from tests.test_util import verify_fixture

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client(app, lnd):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


def check_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, response.text
    return response


def verify_response(response, name, status_code=None):
    if status_code is not None:
        check_response(response, status_code)
    data = dict(status_code=response.status_code, json=response.json())
    verify_fixture(name, data)


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


@pytest.mark.vcr(before_record_request=remove_credentials_and_testclient, before_record_response=remove_url)
async def test_create_donation(client, db):
    async with db.rollback():
        response = await client.post(
            "/api/v1/donate",
            json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
        )
        verify_response(response, 'create-donation', 200)
