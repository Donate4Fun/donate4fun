import uuid
import time
import json
from contextlib import asynccontextmanager
from datetime import datetime

import anyio
import pytest
from authlib.jose import jwt
from httpx import AsyncClient
from vcr.filters import replace_query_parameters
from asgi_testclient import TestClient
from sqlalchemy import select

from donate4fun.api import DonateRequest, DonateResponse, DonationPaidResponse
from donate4fun.lnd import monitor_invoices, LndClient
from donate4fun.settings import LndSettings
from donate4fun.db import Database

from tests.test_util import verify_fixture
from tests.fixtures import *  # noqa


@pytest.fixture
async def user_token(settings, donator_id):
    return jwt.encode(
        dict(alg='HS256'),
        dict(donator=str(donator_id), exp=int(time.time()) + 10 ** 6),
        settings.jwt_secret,
    ).decode()


@pytest.fixture
async def client(app, user_token):
    async with AsyncClient(app=app, base_url="http://test", cookies=dict(session=user_token)) as client:
        yield client


class NestedDb(Database):
    def __init__(self, db_session):
        self.db_session = db_session
        self.session_maker = db_session.db.session_maker

    @asynccontextmanager
    async def session(self):
        async with self.db_session.savepoint() as nested:
            yield nested


@pytest.fixture
def asgi_client(app, user_token):
    #app.db = NestedDb(db_session)
    return TestClient(app, cookies=dict(session=user_token))


@pytest.fixture
async def payer_lnd():
    return LndClient(LndSettings(url='http://localhost:10002'))


def check_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, response.text
    return response


def verify_response(response, name, status_code=None):
    if status_code is not None:
        check_response(response, status_code)
    data = dict(status_code=response.status_code, json=response.json())
    verify_fixture(data, name)


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_latest_donations(asgi_client, db_session, paid_donation_fixture):
    asgi_client.app.db = NestedDb(db_session)
    response = await asgi_client.get("/api/v1/latest-donations")
    verify_response(response, 'latest-donations', 200)


async def test_create_donation_unsupported_target(asgi_client):
    response = await asgi_client.post("/api/v1/donate", json=DonateRequest(amount=100, target='https://asdzxc.com').dict())
    verify_response(response, 'create-donation-unsupported_target', 400)


async def test_create_donation_unsupported_youtube_url(asgi_client):
    response = await asgi_client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://youtube.com/azxcasd').dict(),
    )
    verify_response(response, 'create-donation-unsupported_youtube_url', 400)


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


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate(asgi_client, db_session, freeze_uuid):
    donate_response = await asgi_client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    # Reset dynamic fields
    resp_json = donate_response.json()
    resp_json['donation']['r_hash'] = None
    resp_json['payment_request'] = None
    donate_response._content = json.dumps(resp_json).encode()
    verify_response(donate_response, 'donate', 200)


async def test_get_donation(asgi_client, donation_fixture):
    donation_response = await asgi_client.get(f"/api/v1/donation/{donation_fixture.id}")
    verify_response(donation_response, 'get-donation')


@mark_vcr
@pytest.mark.skip(reason="Only HODL invoices (not implemented)")
@pytest.mark.freeze_time('2022-05-31T12:54:19')
async def test_cancel_donation(asgi_client, app, db_session, freeze_uuid):
    donate_response = await asgi_client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=10, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    # verify_response(donate_response, "cancel-donation-donate-response")
    donation_id = donate_response.json()['id']
    async with anyio.create_task_group() as tg, asgi_client.ws_session(f"/api/v1/donation/subscribe/{donation_id}") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        cancel_response = await asgi_client.post(f"/api/v1/donation/cancel/{donation_id}")
        verify_response(cancel_response, "cancel-donation-cancel-response")
        ws_response = []
        while True:
            resp = await ws.receive_json()
            ws_response.append(resp)
        verify_fixture(ws_response, "cancel-donation-subscribe")


#@mark_vcr
#@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_full(asgi_client, app, freeze_uuid: uuid.UUID, payer_lnd: LndClient):
    donation_id = freeze_uuid
    donate_response: DonateResponse = await asgi_client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=20, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    check_response(donate_response, 200)
    assert donate_response.json()['donation']['id'] == str(donation_id)
    payment_request = donate_response.json()['payment_request']
    print(payment_request)
    #verify_response(donate_response, 'payment-donate')
    async with anyio.create_task_group() as tg, asgi_client.ws_session(f"/api/v1/donation/subscribe/{donation_id}") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        await payer_lnd.pay_invoice(payment_request, timeout=5)
        ws_response = []
        while True:
            response = DonationPaidResponse.parse_obj(await ws.receive_json())
            # Reset dynamic fields
            donation = response.donation
            donation.r_hash = None
            donation.paid_at = None
            donation.created_at = None
            ws_response.append(response)
            if response.status == 'ok':
                break
        verify_fixture(ws_response, "payment-subscribe")
        tg.cancel_scope.cancel()
    donation_response = await asgi_client.get(f"/api/v1/donation/{donation_id}")
    verify_response(donation_response, "payment-donation")


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_websocket(asgi_client, donation_fixture, db_session):
    messages = []
    asgi_client.app.db = NestedDb(db_session)
    async with asgi_client.ws_session(f'/api/v1/donation/subscribe/{donation_fixture.id}') as ws:
        await db_session.donation_paid(r_hash=donation_fixture.r_hash, amount=100, paid_at=datetime.utcnow())
        msg = await ws.receive_json()
        messages.append(msg)
    verify_fixture(messages, "websocket-messages")


async def test_nested(db_session):
    await db_session.execute(select(1))
    async with NestedDb(db_session).session() as nested:
        await nested.execute(select(1))
        try:
            async with NestedDb(nested).session() as nested2:
                await nested2.execute(select(1))
                raise Exception
        except Exception:
            pass
    await db_session.execute(select(1))
