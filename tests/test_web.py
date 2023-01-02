from uuid import UUID
import pytest

import psutil

from donate4fun.models import YoutubeChannel, DonateRequest

from tests.test_util import verify_response, check_response, login_to, mark_vcr
from tests.fixtures import find_unused_port, app_serve


@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_sitemap(client, db):
    async with db.session() as db_session:
        await db_session.save_youtube_channel(
            YoutubeChannel(
                title='test channel',
                id=UUID(int=0),
                channel_id='UCxxx',
            )
        )
    response = await client.get('/sitemap.xml')
    verify_response(response, 'sitemap')


@mark_vcr
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


async def test_twitter_donation_image(client, settings, twitter_account, webapp, rich_donator):
    login_to(client, settings, rich_donator)
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
