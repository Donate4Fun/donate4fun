from datetime import datetime
from uuid import UUID

import httpx
import pytest

from donate4fun.models import (
    DonateRequest, TwitterAccount, TwitterAccountOwned, Donator, TwitterTweet, DonateResponse, DonationPaidRequest,
    PayInvoiceResult, DonationPaidRouteInfo, Donation,
)
from donate4fun.twitter import query_or_fetch_twitter_account
from donate4fun.lnd import lnd, monitor_invoices, PayInvoiceError
from donate4fun.types import PaymentRequest, LightningAddress
from donate4fun.db import db as db_var
from tests.test_util import verify_response, mark_vcr, check_notification, login_to, check_response
from tests.fixtures import find_unused_port, app_serve, make_registered_donator, create_db


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_author(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://twitter.com/donate4_fun').dict(),
    )
    verify_response(donate_response, 'donate_twitter_author', 200)


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_tweet(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(
            amount=100,
            target='https://twitter.com/donate4_fun/status/1583074363787444225',
            donator_twitter_handle='donate4_fun',
        ).dict(),
    )
    verify_response(donate_response, 'donate_twitter_tweet', 200)


@pytest.mark.parametrize('use_rich_donator', [True, False])
@pytest.mark.parametrize('amount', [10, 10 ** 8])
async def test_donate_tweet_with_lightning_address(
    client, db, payer_lnd, rich_donator, settings, app, monkeypatch, use_rich_donator: bool, amount: int,
):
    """
    There are multiple cases:
      local donator, local receiver   <- trivial case, should be the same as without lightning address
      local donator, remote receiver  <- we request and pay lightning invoice, deduce local balance. We test this
      remote donator, local receiver  <- we generate invoice, wait for the payment and increase local balance
                                         It isn't supported currently (until we implement local lightning addreses)
      remote donator, remote receiver <- we request lightning invoice and pass it to requestor, donation
                                         is created but balances are unchanged. We test this.
      remote donator means that donator pays using webln.
      We currently do not support local receivers. To emulate remote receiver we override lnd context var with payer_lnd
      so that locally created invoice could be pai
    """
    # Disable validation to allow to pass port
    regexp_with_port = r'^[a-z0-9-_.]+@(((?!\-))(xn\-\-)?[a-z0-9\\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\\-]{1,61}|[a-z0-9\-]{1,30})(\.[a-z]{2,})?(:\d{1,5})?$'  # noqa
    monkeypatch.setattr(LightningAddress, 'regexp', regexp_with_port)
    settings.lnurlp.max_sendable_sats = amount

    # Patch lightning address getter
    orig_get = httpx.AsyncClient.get

    async def patched_get(self_, url: str, **kwargs):
        """
        Lightning addresses are always using https:// but we don't use https in tests
        """
        return await orig_get(self_, url.replace('https://', 'http://'), **kwargs)
    monkeypatch.setattr(httpx.AsyncClient, 'get', patched_get)

    port = find_unused_port()
    async with create_db('donate4fun-test-receiver') as db2:
        async with db2.session() as db_session:
            receiver: Donator = await make_registered_donator(db2, UUID(int=2))
            receiver.lightning_address = f'some_name@localhost:{port}'
            await db_session.save_donator(receiver)
        async with db.session() as db_session:
            account = TwitterAccount(
                user_id=0,
                handle='handle',
                lightning_address=receiver.lightning_address,
                last_fetched_at=datetime.utcnow(),
            )
            tweet = TwitterTweet(tweet_id=0)
            await db_session.save_twitter_account(account)
            await db_session.get_or_create_tweet(tweet)

        settings.frontend_port = port
        settings.base_url = f'http://localhost:{port}'

        async def app_wrapper(*args):
            with lnd.assign(payer_lnd), db_var.assign(db2):
                return await app(*args)
        # Because we are running two apps with the same DB there will be two
        # Donation records - one for "outgoing" donation and one for "incoming" donation.
        # Another app is needed because the main app makes http request to the lightning address provider (new app)
        async with app_serve(app_wrapper, port):
            if use_rich_donator:
                login_to(client, settings, rich_donator)
            async with monitor_invoices(payer_lnd, db2):
                donate_response = DonateResponse(**check_response(await client.post(
                    "/api/v1/donate",
                    json=DonateRequest(
                        amount=amount,
                        target=f'https://twitter.com/{account.handle}/status/{tweet.tweet_id}',
                        donator_twitter_handle='handle',
                    ).dict(),
                )).json())
                donation = donate_response.donation
                assert (donation.r_hash is None) != (donate_response.payment_request is None)
                if donation.r_hash is not None:
                    assert donation.paid_at != None  # noqa
                    assert donation.fee_msat == 1000
                    assert donation.claimed_at == donation.paid_at
                    me_response = await client.get('/api/v1/donator/me')
                    check_response(me_response)
                    assert me_response.json()['donator']['balance'] < rich_donator.balance - amount
                    failed_to_pay = False
                else:
                    invoice: PaymentRequest = donate_response.payment_request
                    try:
                        async with check_notification(client, 'donation', donation.id):
                            pay_result: PayInvoiceResult = await lnd.pay_invoice(invoice)
                            assert pay_result.payment_hash == donation.transient_r_hash
                            returned_donation = Donation(**check_response(await client.post(
                                f'/api/v1/donation/{donation.id}/paid',
                                json=DonationPaidRequest(
                                    paymentHash=pay_result.payment_hash.as_hex,
                                    preimage=pay_result.payment_preimage.as_hex,
                                    route=DonationPaidRouteInfo(
                                        total_amt=pay_result.value_sat,
                                        total_fees=pay_result.fee_sat,
                                    ),
                                ).dict(),
                            )).json())
                            assert returned_donation.fee_msat == 1000
                            assert returned_donation.paid_at != None  # noqa
                            assert returned_donation.claimed_at == returned_donation.paid_at
                    except PayInvoiceError as exc:
                        assert exc.args[0] == 'FAILURE_REASON_INSUFFICIENT_BALANCE'
                        failed_to_pay = True
                    else:
                        failed_to_pay = False
        async with db2.session() as db_session:
            new_receiver = await db_session.query_donator(id=receiver.id)
            if failed_to_pay:
                assert new_receiver.balance == 0
            else:
                assert new_receiver.balance == amount


async def test_link_twitter_account(db_session):
    donator = Donator(id=UUID(int=0))
    reference_accounts = []
    for i in range(3):
        account = TwitterAccount(
            id=UUID(int=i),
            user_id=i,
            handle="@donate4_fun",
            name="Donate4.Fun",
            profile_image_url="https://thumbnail.url/asd",
        )
        reference_accounts.append(account)
        await db_session.save_twitter_account(account)
        await db_session.link_twitter_account(account, donator)
    twitter_accounts: list[TwitterAccount] = await db_session.query_donator_twitter_accounts(donator.id)
    assert twitter_accounts == reference_accounts
    account: TwitterAccountOwned = await db_session.query_twitter_account(
        id=reference_accounts[0].id, owner_id=UUID(int=0)
    )
    assert account.owner_id == donator.id
    account: TwitterAccountOwned = await db_session.query_twitter_account(
        id=reference_accounts[0].id, owner_id=UUID(int=1)
    )
    assert not account.owner_id == donator.id


@mark_vcr
@pytest.mark.parametrize('params', [dict(handle='donate4_fun'), dict(user_id=12345), dict(handle='twiteis')])
async def test_query_or_fetch_twitter_account(db_session, params):
    await query_or_fetch_twitter_account(db=db_session, **params)


async def test_transfer_from_twitter(client, db, rich_donator, settings):
    login_to(client, settings, rich_donator)
    # Update balance to target value
    async with db.session() as db_session:
        account = TwitterAccount(
            id=UUID(int=0),
            user_id=0,
            handle="@donate4_fun",
            name="Donate4.Fun",
        )
        await db_session.save_twitter_account(account)
        donation = Donation(amount=100, twitter_account=account, donator=rich_donator)
        await db_session.create_donation(donation)
        await db_session.donation_paid(donation_id=donation.id, amount=100, paid_at=datetime.now())
        donation = await db_session.query_donation(id=donation.id)
        await db_session.link_twitter_account(donator=rich_donator, twitter_author=account)

    resp = await client.post(f'/api/v1/twitter/account/{account.id}/transfer')
    check_response(resp, 200)
    amount = resp.json()['amount']
    assert amount == donation.amount
    async with db.session() as db_session:
        account: TwitterAccount = await db_session.query_twitter_account(user_id=account.id, owner_id=rich_donator.id)
        assert account.balance == 0
        donator = await db_session.query_donator(id=rich_donator.id)
        assert donator.balance == amount
        donation = await db_session.query_donation(id=donation.id)
        assert donation.claimed_at != None  # noqa
