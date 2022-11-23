import socket
from uuid import UUID
import pytest

from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config

from donate4fun.models import YoutubeChannel, DonateRequest
from donate4fun.core import as_task

from tests.test_util import verify_response, check_response


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


async def test_donate_redirect(client):
    response = await client.get('/d/UCk2OzObixhe_mbMfMQGLuJw')
    check_response(response, 302)


async def test_index_page(client):
    response = await client.get('/')
    verify_response(response, 'index-page', 200)


async def test_twitter_page(client, twitter_account):
    response = await client.get(f'/twitter/{twitter_account.id}')
    verify_response(response, 'twitter-page', 200)


def find_unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(('localhost', 0))
        return sock.getsockname()[1]


@as_task
async def app_serve(app, settings):
    port = find_unused_port()
    settings.hypercorn['bind'] = f'localhost:{port}'
    hyper_config = Config.from_mapping(settings.hypercorn)
    await hypercorn_serve(app, hyper_config)


async def test_twitter_share_image_page(client):
    profile_image = 'https://github.githubassets.com/images/modules/open_graph/github-mark.png'
    response = await client.get(
        '/preview/twitter-account-sharing.html', params=dict(handle='handle', profile_image=profile_image),
    )
    verify_response(response, 'twitter-share-image-source', 200)


async def test_twitter_share_image(client, twitter_account, app, settings):
    async with app_serve(app, settings):
        response = await client.get(f'/preview/twitter/{twitter_account.id}')
        verify_response(response, 'twitter-share-image', 200)


async def test_twitter_account_redirect(client, freeze_uuids):
    response = await client.get('/tw/donate4_fun')
    check_response(response, 302)
    assert response.headers['location'].split('/')[-1] == str(UUID(int=1))


async def test_422(client):
    response = await client.get('/twitter/unexistent')
    verify_response(response, 'twitter-422', 422)


async def test_404(client):
    response = await client.get(f'/donation/{UUID(int=0)}')
    verify_response(response, 'twitter-404', 404)


async def test_twitter_donation_image(client, twitter_account, app, settings, rich_donator):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(
            amount=100,
            target='https://twitter.com/donate4_fun/status/1583074363787444225',
            donator_twitter_handle='nbryskin',
        ).dict(),
    )
    check_response(donate_response, 200)

    async with app_serve(app, settings):
        response = await client.get(f'/preview/donation/{donate_response.json()["donation"]["id"]}')
        verify_response(response, 'twitter-donation-share-image', 200)
