import json
from uuid import UUID
from datetime import datetime
from functools import partial
from urllib.parse import urlparse, parse_qs, urlunparse
from contextlib import asynccontextmanager

import anyio
import pytest
import ecdsa
from anyio.abc import TaskStatus
from vcr.filters import replace_query_parameters
from lnurl.helpers import _lnurl_decode

from donate4fun.api import DonateRequest, DonateResponse, WithdrawResponse, LnurlWithdrawResponse
from donate4fun.lnd import monitor_invoices, LndClient, Invoice
from donate4fun.settings import LndSettings
from donate4fun.models import Donation, YoutubeChannel, Donator
from donate4fun.db import Notification

from tests.test_util import verify_fixture, verify_response, check_response, freeze_time
from tests.fixtures import Session, Settings


@pytest.fixture
async def payer_lnd():
    return LndClient(LndSettings(url='http://localhost:10002', lnurl_base_url='http://test'))


@freeze_time
async def test_latest_donations(client, paid_donation_fixture, freeze_request_hash_json):
    response = await client.get("/api/v1/donations/latest")
    verify_response(response, 'latest-donations', 200)


@freeze_time
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


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_video(
    client, db_session, freeze_donation_id, freeze_request_hash, freeze_payment_request, freeze_youtube_channel_id,
    freeze_youtube_video_id,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/watch?v=7qH7WMzqOlU&t=692s').dict(),
    )
    verify_response(donate_response, 'donate_video', 200)


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
    async with anyio.create_task_group() as tg, client.ws_session(f"/api/v1/donation/{donation_id}/subscribe") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        cancel_response = await client.post(f"/api/v1/donation/{donation_id}/cancel")
        verify_response(cancel_response, "cancel-donation-cancel-response")
        ws_response = []
        while True:
            resp = await ws.receive_json()
            ws_response.append(resp)
        verify_fixture(ws_response, "cancel-donation-subscribe")


@asynccontextmanager
async def check_notification(client, topic: str, id_: UUID):
    async with client.ws_session(f"/api/v1/subscribe/{topic}:{id_}") as ws:
        yield
        with anyio.fail_after(5):
            notification = Notification.parse_obj(await ws.receive_json())
        assert notification.status == 'OK'
        assert notification.id == id_


async def test_donate_full(
    client, app, freeze_donation_id, freeze_youtube_channel_id, payer_lnd: LndClient,
    freeze_request_hash_json, pubsub,
):
    video_id = 'rq2SVMXEMPI'
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=20, target=f'https://www.youtube.com/watch?v={video_id}').dict(),
    )
    check_response(donate_response, 200)
    assert donate_response.json()['donation']['id'] == str(freeze_donation_id)
    payment_request = donate_response.json()['payment_request']
    check_donation_notification = check_notification(client, 'donation', freeze_donation_id)
    check_video_notification = check_notification(client, 'youtube-video-by-vid', video_id)
    async with monitor_invoices(app.lnd, app.db), check_donation_notification, check_video_notification:
        await payer_lnd.pay_invoice(payment_request)
    donation_response = await client.get(f"/api/v1/donation/{freeze_donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa


def login_to(client, settings: Settings, donator: Donator):
    # Relogin to rich donator (with balance > 0)
    client.cookies = dict(session=Session(donator=donator.id, jwt_secret=settings.jwt_secret).to_jwt())


async def test_fulfill(
    client, app, freeze_donation_id, payer_lnd: LndClient, settings,
    freeze_request_hash_json, pubsub, registered_donator,
):
    amount = 30
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=json.loads(DonateRequest(amount=amount, receiver_id=registered_donator.id).json()),
    )
    check_response(donate_response, 200)
    assert donate_response.json()['donation']['id'] == str(freeze_donation_id)
    payment_request = donate_response.json()['payment_request']
    check_donation_notification = check_notification(client, 'donation', freeze_donation_id)
    check_donator_notification = check_notification(client, 'donator', registered_donator.id)
    async with monitor_invoices(app.lnd, app.db), check_donation_notification, check_donator_notification:
        await payer_lnd.pay_invoice(payment_request)
    donation_response = await client.get(f"/api/v1/donation/{freeze_donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa
    login_to(client, settings, registered_donator)
    me_response = await client.get("/api/v1/donator/me")
    check_response(me_response, 200)
    assert me_response.json()['donator']['balance'] == amount


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_websocket(client, unpaid_donation_fixture, db, freeze_request_hash_json, pubsub):
    messages = []
    # Test with two concurrent websockets (there were bugs with it)
    donation_ws_ctx_1 = client.ws_session(f'/api/v1/subscribe/donation:{unpaid_donation_fixture.id}')
    donation_ws_ctx_2 = client.ws_session(f'/api/v1/subscribe/donation:{unpaid_donation_fixture.id}')
    async with donation_ws_ctx_1 as ws_1, donation_ws_ctx_2 as ws_2:
        async with db.session() as db_session:
            await db_session.donation_paid(donation_id=unpaid_donation_fixture.id, amount=100, paid_at=datetime.utcnow())
        msg_1 = await ws_1.receive_json()
        msg_2 = await ws_2.receive_json()
        assert msg_1 == msg_2
        messages.append(msg_1)
    verify_fixture(messages, "websocket-messages")


async def test_state(client):
    response = await client.get("/api/v1/status")
    verify_response(response, "status", 200)


async def test_withdraw_unproved(client, unpaid_donation_fixture):
    channel_id = unpaid_donation_fixture.youtube_channel.id
    resp = await client.get(f'/api/v1/youtube-channel/{channel_id}/withdraw')
    check_response(resp, 403)


async def wait_for_payment(lnd_client, r_hash, *, task_status: TaskStatus):
    async for data in lnd_client.subscribe("/v1/invoices/subscribe"):
        if data is None:
            task_status.started()
            continue
        invoice: Invoice = Invoice(**data['result'])
        assert invoice.r_hash == r_hash
        assert invoice.state == 'SETTLED'
        break


async def wait_for_withdrawal(
    client, youtube_channel_id: UUID, amount_diff: int, status: str, message: str, task_status: TaskStatus,
):
    async with client.ws_session(f"/api/v1/subscribe/withdrawal:{youtube_channel_id}") as ws:
        task_status.started()
        msg = await ws.receive_json()
        notification = Notification(**msg)
        assert notification.id == youtube_channel_id
        assert notification.status == status
        assert notification.message == message


def login_youtuber(client, client_session, youtube_channel):
    client_session.youtube_channels = [youtube_channel.id]
    client.cookies['session'] = client_session.to_jwt()


@pytest.mark.parametrize('balance, amount_diff, balance_diff, status, message, is_ok', [
    (20, -1, 0, 'OK', None, True), (20, 0, 0, 'OK', None, True),
    (20, 1, 0, 'OK', None, False), (20, 0, -1, 'OK', None, False),
    (10**8, 0, 0, 'ERROR', 'FAILURE_REASON_INSUFFICIENT_BALANCE', False),
])
async def test_withdraw(
    client, paid_donation_fixture, client_session, payer_lnd, balance, amount_diff, balance_diff, status,
    message, is_ok, settings, db, pubsub,
):
    channel_id = paid_donation_fixture.youtube_channel.id
    # Update balance to target value
    async with db.session() as db_session:
        await db_session.link_youtube_channel(
            donator=Donator(id=client_session.donator), youtube_channel=paid_donation_fixture.youtube_channel,
        )
        await db_session.withdraw(youtube_channel_id=channel_id, amount=paid_donation_fixture.amount - balance)
    resp = await client.get(f'/api/v1/youtube-channel/{channel_id}/withdraw')
    check_response(resp, 200)
    response = WithdrawResponse(**resp.json())
    assert response.amount == balance
    decoded_url = _lnurl_decode(response.lnurl)
    lnurl_response = await client.get(decoded_url)
    lnurl_data = LnurlWithdrawResponse(**lnurl_response.json())
    assert lnurl_data.min_sats == settings.min_withdraw
    assert lnurl_data.max_sats == balance
    invoice: Invoice = await payer_lnd.create_invoice(
        memo=lnurl_data.default_description,
        value=balance + amount_diff,
    )
    if balance_diff:
        async with db.session() as db_session:
            await db_session.withdraw(youtube_channel_id=channel_id, amount=-balance_diff)
    async with anyio.create_task_group() as tg:
        client.app.task_group = tg
        if is_ok:
            await tg.start(wait_for_payment, payer_lnd, invoice.r_hash)
            await tg.start(partial(
                wait_for_withdrawal,
                client=client,
                amount_diff=amount_diff,
                youtube_channel_id=paid_donation_fixture.youtube_channel.id,
                status=status,
                message=message,
            ))
        callback_response = await client.get(lnurl_data.callback, params=dict(k1=lnurl_data.k1, pr=invoice.payment_request))
        check_response(callback_response, 200)
        assert callback_response.json()['status'] == 'OK' if is_ok else 'ERROR', callback_response.json()['reason']
    # Check final balance
    async with db.session() as db_session:
        youtube_channel: YoutubeChannel = await db_session.query_youtube_channel(youtube_channel_id=channel_id)
        assert youtube_channel.balance == -amount_diff if is_ok else balance


@pytest.mark.parametrize('case_name,_registered_donator', [
    ('signup', None),
    ('signin', pytest.lazy_fixture('registered_donator')),
])
async def test_lnauth(client, case_name, _registered_donator, donator_id, pubsub):
    """
    donator_id: temporary donator id (like those given to user when he opens the site without session)
    """
    lnauth_response = await client.get('/api/v1/lnauth')
    lnurl = _lnurl_decode(lnauth_response.json()['lnurl'])
    lnurl_parsed = urlparse(lnurl)
    query = parse_qs(lnurl_parsed.query, strict_parsing=True)
    assert query['tag'] == ['login']
    assert query['action'] == ['link']
    k1 = query['k1'][0]
    sk = ecdsa.SigningKey.generate(entropy=ecdsa.util.PRNG(b'seed'), curve=ecdsa.SECP256k1)
    signature = sk.sign_digest_deterministic(bytes.fromhex(k1), sigencode=ecdsa.util.sigencode_der)
    callback_url = urlunparse(list(lnurl_parsed)[:3] + [''] * 3)
    async with client.ws_session(f'/api/v1/subscribe/donator:{donator_id}') as ws:
        callback_response = await client.get(callback_url, params=dict(
            sig=signature.hex(),
            key=sk.verifying_key.to_string().hex(),
            **{k: v[0] for k, v in query.items()},
        ))
        assert callback_response.json()['status'] == 'OK'
        verify_response(callback_response, 'lnauth-callback', 200)
        msg = await ws.receive_json()
        assert msg['status'] == 'ok'
        registered_donator_jwt = msg['message']

    update_session_resp = await client.post('/api/v1/update-session', json=dict(creds_jwt=registered_donator_jwt))
    check_response(update_session_resp)
    me_response = await client.get('/api/v1/donator/me')
    verify_response(me_response, f'lnauth-me-{case_name}', 200)
    new_donator = Donator.parse_obj(me_response.json()['donator'])
    assert new_donator.lnauth_pubkey == sk.verifying_key.to_string().hex()


async def test_youtube_video(client):
    youtube_videoid = 'sLcdanDHPjM'
    origin = 'https://youtube.com'
    response = await client.get(f"/api/v1/youtube-video/{youtube_videoid}", headers=dict(origin=origin))
    verify_response(response, 'youtube-video', 200)
    assert response.headers['access-control-allow-origin'] == origin


async def test_youtube_video_no_cors(client):
    youtube_videoid = 'sLcdanDHPjM'
    response = await client.get(f"/api/v1/youtube-video/{youtube_videoid}", headers=dict(origin="https://unallowed.com"))
    check_response(response, 200)
    assert 'Access-Control-Allow-Origin' not in response.headers


async def test_donate_from_balance(
    client, app, freeze_donation_id, freeze_youtube_channel_id, pubsub, rich_donator, settings,
):
    login_to(client, settings, rich_donator)
    video_id = 'rq2SVMXEMPI'
    amount = 30
    check_donation_notification = check_notification(client, 'donation', freeze_donation_id)
    check_video_notification = check_notification(client, 'youtube-video-by-vid', video_id)
    async with check_donation_notification, check_video_notification:
        donate_response: DonateResponse = await client.post(
            "/api/v1/donate",
            json=DonateRequest(amount=amount, target=f'https://www.youtube.com/watch?v={video_id}').dict(),
        )
        check_response(donate_response, 200)
        donation = donate_response.json()['donation']
        assert donation['id'] == str(freeze_donation_id)
        assert donation['r_hash'] == None  # noqa
    donation_response = await client.get(f"/api/v1/donation/{freeze_donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa
    me_response = await client.get('/api/v1/donator/me')
    check_response(me_response, 200)
    assert me_response.json()['donator']['balance'] == rich_donator.balance - amount
