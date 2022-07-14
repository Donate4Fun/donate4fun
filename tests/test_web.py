from uuid import UUID
import pytest

from donate4fun.models import YoutubeChannel

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
