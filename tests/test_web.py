from uuid import UUID
from donate4fun.models import YoutubeChannel

from tests.test_util import verify_response


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
