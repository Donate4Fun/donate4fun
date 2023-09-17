from uuid import UUID
import pytest

import psutil
from asgi_testclient import TestClient
from furl import furl

from donate4fun.models import YoutubeChannel, DonateRequest, SocialAccount, SocialProviderId
from donate4fun.social import SocialProvider
from donate4fun.db_youtube import YoutubeDbLib
from donate4fun.donation import LnurlpClient
from donate4fun.lnd import lnd, monitor_invoices_step
from donate4fun.types import Satoshi

from tests.test_util import verify_response, check_response, login_to, mark_vcr, freeze_time, check_notification
from tests.fixtures import find_unused_port, app_serve


@freeze_time
async def test_sitemap(client, db):
    async with db.session() as db_session:
        await YoutubeDbLib(db_session).save_account(
            YoutubeChannel(
                title='test channel',
                id=UUID(int=0),
                channel_id='UCxxx',
            )
        )
    response = await client.get('/sitemap.xml')
    verify_response(response, 'sitemap')


@mark_vcr
@pytest.mark.freezed_vcr
async def test_donate_redirect(client):
    response = await client.get('/d/UCk2OzObixhe_mbMfMQGLuJw')
    check_response(response, 302)


async def test_index_page(client):
    response = await client.get('/')
    verify_response(response, 'index-page', 200)


async def test_twitter_page(client, twitter_account):
    response = await client.get(f'/twitter/{twitter_account.id}')
    verify_response(response, 'twitter-page', 200)


@pytest.fixture
async def webapp(app, settings):
    port = find_unused_port()
    settings.frontend_port = port
    settings.api_port = port
    async with app_serve(app, port):
        yield


async def test_twitter_share_image_page(client):
    profile_image = 'https://github.githubassets.com/images/modules/open_graph/github-mark.png'
    response = await client.get(
        '/preview/twitter-account-sharing.html', params=dict(handle='handle', profile_image=profile_image),
    )
    verify_response(response, 'twitter-share-image-source', 200)


async def test_screenshot_browser_crash(client, twitter_account, webapp):
    check_response(await client.get(f'/preview/twitter/{twitter_account.id}'))
    for child in psutil.Process().children(recursive=True):
        if child.name() == 'name':
            child.kill()
            break
    check_response(await client.get(f'/preview/twitter/{twitter_account.id}'))


async def test_twitter_share_image(client, twitter_account, webapp):
    response = await client.get(f'/preview/twitter/{twitter_account.id}')
    verify_response(response, 'twitter-share-image', 200)


@mark_vcr
async def test_twitter_account_redirect(client, twitter_account):
    response = await client.get(f'/tw/{twitter_account.handle}')
    check_response(response, 302)
    assert response.headers['location'].split('/')[-1] == str(UUID(int=1))


async def test_422(client):
    response = await client.get('/twitter/unexistent')
    verify_response(response, 'twitter-422', 422)


async def test_404(client):
    response = await client.get(f'/donation/{UUID(int=0)}')
    verify_response(response, 'twitter-404', 404)


@mark_vcr
async def test_twitter_donation_image(client, settings, twitter_account, webapp, rich_donator, monkeypatch):
    login_to(client, settings, rich_donator)
    # https://peter.sh/experiments/chromium-command-line-switches/
    chromium_flags = [
        '--disable-gpu',
        '--font-render-hinting=none',
        '--disable-skia-runtime-opts',
        '--disable-font-subpixel-positioning',
        '--disable-lcd-text',
    ]
    monkeypatch.setattr('donate4fun.screenshot.chromium_flags', lambda: chromium_flags)
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(
            amount=100,
            target=f'https://twitter.com/{twitter_account.handle}/status/1583074363787444225',
            donator_twitter_handle=twitter_account.handle,
        ).dict(),
    )
    check_response(donate_response, 200)

    response = await client.get(f'/preview/donation/{donate_response.json()["donation"]["id"]}')
    verify_response(response, 'twitter-donation-share-image', 200)


class TestLnurlpClient(TestClient, LnurlpClient):
    """
    Try to emulate httpx.AsyncClient using TestClient
    """
    async def get(self, url: str, **kwargs):
        return await super().get(url)


@mark_vcr
@pytest.mark.parametrize('social_provider,username', [
    (SocialProviderId.twitter, 'Bryskin2'),
    (SocialProviderId.twitter, 'nbryskin'),
    (SocialProviderId.youtube, '@donate4fun'),
    # (SocialProviderId.github, 'nikicat'),  # NotImplemented
])
async def test_lnurlp(app, db, payer_lnd, client, social_provider: SocialProviderId, username: str):
    lnurlp_client = LnurlpClient(app=app, base_url="http://test")
    response = await lnurlp_client.get(f'/lnurlp/{social_provider.value}/{username}')
    check_response(response, 302)
    amount: Satoshi = 100
    metadata = await lnurlp_client.fetch_metadata(str(furl(response.headers['location']).path))
    if furl(metadata['callback']).host != 'test':
        # If social account has a lightning address then don't try to pay to it from a regtest network
        return
    pay_req = await lnurlp_client.fetch_invoice(metadata, amount=amount, name='some name', comment='some comment')
    async with monitor_invoices_step(lnd, db), check_notification(client, topic='donations'):
        await payer_lnd.pay_invoice(pay_req)
    async with db.session() as db_session:
        provider = SocialProvider.create(social_provider)
        db_lib = provider.wrap_db(db_session)
        account: SocialAccount = await provider.query_or_fetch_account(db_lib, handle=username)
        assert account.balance == amount
