import time
from uuid import UUID
from datetime import datetime

import anyio
import pytest
from anyio.abc import TaskStatus
from authlib.jose import jwt
from vcr.filters import replace_query_parameters
from asgi_testclient import TestClient
from lnurl.helpers import _lnurl_decode

from donate4fun.api import DonateRequest, DonateResponse, WithdrawResponse, LnurlWithdrawResponse
from donate4fun.lnd import monitor_invoices, LndClient, Invoice
from donate4fun.settings import LndSettings
from donate4fun.models import Donation, BaseModel

from tests.test_util import verify_fixture


class Session(BaseModel):
    donator: UUID
    youtube_channels: list[UUID] = []
    jwt_secret: str

    def to_jwt(self):
        return jwt.encode(
            dict(alg='HS256'),
            dict(
                donator=str(self.donator),
                youtube_channels=[str(channel) for channel in self.youtube_channels],
                exp=int(time.time()) + 10 ** 6,
            ),
            self.jwt_secret,
        ).decode()


@pytest.fixture
def client_session(donator_id, settings):
    return Session(donator=donator_id, jwt_secret=settings.jwt_secret)


@pytest.fixture
def client(app, client_session):
    return TestClient(app, cookies=dict(session=client_session.to_jwt()))


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
async def test_latest_donations(client, paid_donation_fixture, freeze_request_hash_json):
    response = await client.get("/api/v1/donations/latest")
    verify_response(response, 'latest-donations', 200)


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donator_donations(client, paid_donation_fixture, freeze_request_hash_json, db):
    async with db.session() as db_session:
        await db_session.save_donator(paid_donation_fixture.donator)
    response = await client.get(f"/api/v1/donations/by-donator/{paid_donation_fixture.donator.id}")
    verify_response(response, 'donator-donations', 200)


async def test_create_donation_unsupported_target(client):
    response = await client.post("/api/v1/donate", json=DonateRequest(amount=100, target='https://asdzxc.com').dict())
    verify_response(response, 'create-donation-unsupported_target', 400)


async def test_create_donation_unsupported_youtube_url(client):
    response = await client.post(
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
async def test_donate(
    client, db_session, freeze_donation_id, freeze_request_hash, freeze_payment_request, freeze_youtube_channel_id,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    verify_response(donate_response, 'donate', 200)


@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_get_donation(client, unpaid_donation_fixture: Donation, freeze_request_hash_json, freeze_payment_request):
    donation_response = await client.get(f"/api/v1/donation/{unpaid_donation_fixture.id}")
    verify_response(donation_response, 'get-donation', 200)


@mark_vcr
@pytest.mark.skip(reason="Only HODL invoices (not implemented)")
@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_cancel_donation(client, app, db_session, freeze_donation_id):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=10, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    # verify_response(donate_response, "cancel-donation-donate-response")
    donation_id = donate_response.json()['id']
    async with anyio.create_task_group() as tg, client.ws_session(f"/api/v1/donation/subscribe/{donation_id}") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        cancel_response = await client.post(f"/api/v1/donation/cancel/{donation_id}")
        verify_response(cancel_response, "cancel-donation-cancel-response")
        ws_response = []
        while True:
            resp = await ws.receive_json()
            ws_response.append(resp)
        verify_fixture(ws_response, "cancel-donation-subscribe")


async def test_donate_full(
    client, app, freeze_donation_id, freeze_youtube_channel_id, payer_lnd: LndClient,
    freeze_request_hash_json,
):
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=20, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    check_response(donate_response, 200)
    assert donate_response.json()['donation']['id'] == str(freeze_donation_id)
    payment_request = donate_response.json()['payment_request']
    async with anyio.create_task_group() as tg, client.ws_session(f"/api/v1/donation/subscribe/{freeze_donation_id}") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        await payer_lnd.pay_invoice(payment_request, timeout=20)
        ws_response = []
        while True:
            donation = Donation.parse_obj(await ws.receive_json())
            donation.paid_at = datetime(2022, 2, 2)
            donation.created_at = datetime(2022, 2, 2)
            ws_response.append(donation)
            if donation.paid_at is not None:
                break
        verify_fixture(ws_response, "payment-subscribe")
        tg.cancel_scope.cancel()
    donation_response = await client.get(f"/api/v1/donation/{freeze_donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_websocket(client, unpaid_donation_fixture, db, freeze_request_hash_json):
    messages = []
    async with client.ws_session(f'/api/v1/donation/subscribe/{unpaid_donation_fixture.id}') as ws:
        async with db.session() as db_session:
            await db_session.donation_paid(r_hash=unpaid_donation_fixture.r_hash, amount=100, paid_at=datetime.utcnow())
        msg = await ws.receive_json()
        messages.append(msg)
    verify_fixture(messages, "websocket-messages")


async def test_state(client):
    response = await client.get("/api/v1/status")
    verify_response(response, "status", 200)


async def test_withdraw_unproved(client, unpaid_donation_fixture):
    channel_id = unpaid_donation_fixture.youtube_channel.id
    resp = await client.get(f'/api/v1/youtube-channel/{channel_id}/withdraw')
    check_response(resp, 403)


async def wait_for_payment(lnd_client, r_hash, *, task_status: TaskStatus = anyio.TASK_STATUS_IGNORED):
    async for data in lnd_client.subscribe("/v1/invoices/subscribe"):
        if data is None:
            task_status.started()
            continue
        invoice: Invoice = Invoice(**data['result'])
        assert invoice.r_hash == r_hash
        assert invoice.state == 'SETTLED'
        break


def login_youtuber(client, client_session, youtube_channel):
    client_session.youtube_channels = [youtube_channel.id]
    client.cookies['session'] = client_session.to_jwt()


@pytest.mark.parametrize('amount_diff, balance_diff, is_ok', [(-1, 0, True), (0, 0, True), (1, 0, False), (0, -1, False)])
async def test_withdraw(client, paid_donation_fixture, client_session, payer_lnd, amount_diff, balance_diff, is_ok, settings, db):
    login_youtuber(client, client_session, paid_donation_fixture.youtube_channel)
    channel_id = paid_donation_fixture.youtube_channel.id
    resp = await client.get(f'/api/v1/youtube-channel/{channel_id}/withdraw')
    check_response(resp, 200)
    response = WithdrawResponse(**resp.json())
    assert response.amount == paid_donation_fixture.amount
    decoded_url = _lnurl_decode(response.lnurl)
    lnurl_response = await client.get(decoded_url)
    lnurl_data = LnurlWithdrawResponse(**lnurl_response.json())
    assert lnurl_data.min_withdrawable == settings.min_withdraw
    assert lnurl_data.max_withdrawable == paid_donation_fixture.amount
    invoice: Invoice = await payer_lnd.create_invoice(
        memo=lnurl_data.default_description,
        value=paid_donation_fixture.amount + amount_diff,
    )
    if balance_diff:
        async with db.session() as db_session:
            await db_session.withdraw(youtube_channel_id=channel_id, amount=-balance_diff)
    async with anyio.create_task_group() as tg:
        client.app.task_group = tg
        if is_ok:
            await tg.start(wait_for_payment, payer_lnd, invoice.r_hash)
        callback_response = await client.get(lnurl_data.callback, params=dict(k1=lnurl_data.k1, pr=invoice.payment_request))
        check_response(callback_response, 200)
        assert callback_response.json()['status'] == 'OK' if is_ok else 'ERROR', callback_response.json()['reason']
