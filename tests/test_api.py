import json
from functools import partial
from uuid import UUID
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlunparse

import pytest
import ecdsa
import anyio
from lnurl.helpers import _lnurl_decode
from anyio.abc import TaskStatus
from sqlalchemy import update

from donate4fun.api import DonateRequest, DonateResponse, WithdrawResponse, LnurlWithdrawResponse
from donate4fun.lnd import monitor_invoices, LndClient, Invoice, lnd
from donate4fun.models import Donation, Donator, SubscribeEmailRequest
from donate4fun.db import Notification
from donate4fun.db_models import DonatorDb

from tests.test_util import verify_fixture, verify_response, check_response, freeze_time, check_notification, login_to
from tests.fixtures import Settings


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


@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_get_donation(client, unpaid_donation_fixture: Donation, freeze_request_hash_json, freeze_payment_request):
    donation_response = await client.get(f"/api/v1/donation/{unpaid_donation_fixture.id}")
    verify_response(donation_response, 'get-donation', 200)


async def test_fulfill(
    client, app, freeze_uuids, payer_lnd: LndClient, settings,
    freeze_request_hash_json, registered_donator, db
):
    amount = 30
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=json.loads(DonateRequest(amount=amount, receiver_id=registered_donator.id).json()),
    )
    check_response(donate_response, 200)
    donation_id = donate_response.json()['donation']['id']
    assert donation_id == str(UUID(int=1))
    payment_request = donate_response.json()['payment_request']
    check_donation_notification = check_notification(client, 'donation', donation_id)
    check_donator_notification = check_notification(client, 'donator', registered_donator.id)
    async with monitor_invoices(lnd, db), check_donation_notification, check_donator_notification:
        await payer_lnd.pay_invoice(payment_request)
    donation_response = await client.get(f"/api/v1/donation/{donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa
    login_to(client, settings, registered_donator)
    me_response = await client.get("/api/v1/donator/me")
    check_response(me_response, 200)
    assert me_response.json()['donator']['balance'] == amount


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_websocket(client, unpaid_donation_fixture, db, freeze_request_hash_json):
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


@pytest.mark.parametrize('case_name,_registered_donator', [
    ('signup', None),
    ('signin', pytest.lazy_fixture('registered_donator')),
])
async def test_lnauth(client, case_name, _registered_donator, donator_id):
    """
    donator_id: temporary donator id (like those given to user when he opens the site without session)
    """
    nonce = UUID(int=0)
    lnauth_response = check_response(await client.get(f'/api/v1/lnauth/{nonce}'))
    lnurl = _lnurl_decode(lnauth_response.json()['lnurl'])
    lnurl_parsed = urlparse(lnurl)
    query = parse_qs(lnurl_parsed.query, strict_parsing=True)
    assert query['tag'] == ['login']
    assert query['action'] == ['link']
    k1 = query['k1'][0]
    sk = ecdsa.SigningKey.generate(entropy=ecdsa.util.PRNG(b'seed'), curve=ecdsa.SECP256k1)
    signature = sk.sign_digest_deterministic(bytes.fromhex(k1), sigencode=ecdsa.util.sigencode_der)
    callback_url = urlunparse(list(lnurl_parsed)[:3] + [''] * 3)
    async with client.ws_session(f'/api/v1/subscribe/lnauth:{nonce}') as ws:
        callback_response = await client.get(callback_url, params=dict(
            sig=signature.hex(),
            key=sk.verifying_key.to_string().hex(),
            **{k: v[0] for k, v in query.items()},
        ))
        check_response(callback_response)
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


@freeze_time
async def test_subscribe_email(client, db):
    response = await client.post("/api/v1/subscribe-email", json=SubscribeEmailRequest(email="me@example.com").dict())
    check_response(response)
    assert response.json() != None  # noqa


async def test_disconnect_wallet(client, settings: Settings, registered_donator: Donator, db):
    login_to(client, settings, registered_donator)
    response = check_response(await client.get("/api/v1/donator/me"))
    assert response.json()['donator']['lnauth_pubkey'] == registered_donator.lnauth_pubkey
    check_response(await client.post("/api/v1/disconnect-wallet"))
    me_response = check_response(await client.get("/api/v1/donator/me"))
    assert me_response.json()['donator']['lnauth_pubkey'] == None  # noqa


@pytest.mark.parametrize('balance, amount_diff, balance_diff, status, message, is_ok', [
    (20, -1, 0, 'OK', None, True), (20, 0, 0, 'OK', None, True),
    (20, 1, 0, 'OK', None, False), (20, 0, -1, 'OK', None, False),
    (10**8, 0, 0, 'ERROR', 'FAILURE_REASON_INSUFFICIENT_BALANCE', False),
])
async def test_withdraw(
    client, payer_lnd, balance, amount_diff, balance_diff, status,
    message, is_ok, settings, db, registered_donator,
):
    """
    balance is initial donator balance
    amount_diff is a difference between balance and invoice amount
    balance_diff is a difference between balance after initiaing withdrawal and before commiting invoice to emulate double-spend
    """
    donator = registered_donator
    login_to(client, settings, donator)
    async with db.session() as db_session:
        await db_session.execute(
            update(DonatorDb)
            .values(balance=balance)
            .where(DonatorDb.id == donator.id)
        )

    resp = await client.get('/api/v1/me/withdraw')
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
        # Test double-spend
        async with db.session() as db_session:
            await db_session.execute(
                update(DonatorDb)
                .values(balance=DonatorDb.balance + balance_diff)
                .where(DonatorDb.id == donator.id)
            )
    async with anyio.create_task_group() as tg:
        client.app.task_group = tg
        if is_ok:
            await tg.start(wait_for_payment, payer_lnd, invoice.r_hash)
            await tg.start(partial(
                wait_for_withdrawal,
                withdrawal_id=response.withdrawal_id,
                client=client,
                amount_diff=amount_diff,
                status=status,
                message=message,
            ))
        callback_response = await client.get(lnurl_data.callback, params=dict(k1=lnurl_data.k1, pr=invoice.payment_request))
        check_response(callback_response, 200)
        assert callback_response.json()['status'] == 'OK' if is_ok else 'ERROR', callback_response.json()['reason']
        print("wait for task complete")
    # Check final balance
    async with db.session() as db_session:
        donator: Donator = await db_session.query_donator(donator_id=donator.id)
        assert donator.balance == -amount_diff if is_ok else balance


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
    client, withdrawal_id: UUID, amount_diff: int, status: str, message: str, task_status: TaskStatus,
):
    async with client.ws_session(f"/api/v1/subscribe/withdrawal:{withdrawal_id}") as ws:
        task_status.started()
        msg = await ws.receive_json()
        notification = Notification(**msg)
        assert notification.id == withdrawal_id
        assert notification.status == status, notification.message
        assert notification.message == message
