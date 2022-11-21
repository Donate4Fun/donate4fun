from uuid import UUID
import pytest

from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config

from donate4fun.models import YoutubeChannel
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


@as_task
async def app_serve(app, settings):
    hyper_config = Config.from_mapping(settings.hypercorn)
    await hypercorn_serve(app, hyper_config)


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
