from uuid import UUID

import pytest
from donate4fun.models import DonateRequest, TwitterAccount, TwitterAccountOwned, Donator
from donate4fun.twitter import query_or_fetch_twitter_account
from tests.test_util import verify_response, mark_vcr


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
    assert account.is_my
    account: TwitterAccountOwned = await db_session.query_twitter_account(
        id=reference_accounts[0].id, owner_id=UUID(int=1)
    )
    assert not account.is_my


@mark_vcr
@pytest.mark.parametrize('params', [dict(handle='donate4_fun'), dict(user_id=12345)])
async def test_query_or_fetch_twitter_account(db_session, params):
    await query_or_fetch_twitter_account(db=db_session, **params)
