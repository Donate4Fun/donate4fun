import pytest
from donate4fun.models import DonateRequest
from tests.test_util import verify_response


@pytest.mark.vcr()
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_author(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://twitter.com/donate4_fun').dict(),
    )
    verify_response(donate_response, 'donate_twitter_author', 200)


@pytest.mark.vcr()
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_tweet(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://twitter.com/donate4_fun/status/1583074363787444225').dict(),
    )
    verify_response(donate_response, 'donate_twitter_tweet', 200)
