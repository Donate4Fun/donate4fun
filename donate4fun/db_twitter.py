from .db_models import TwitterAuthorDb


class TwitterDbMixin:
    async def get_or_create_author(self, author_id: int, handle: str) -> TwitterAuthorDb:
        resp = await self.execute(
            insert(TwitterAuthorDb)
            .values(
                author_id=youtube_video.youtube_channel.id,
            )
            .on_conflict_do_update(
                index_elements=[TwitterAuthorDb.tweet_id],
                set_={
                    YoutubeVideoDb.title: twitter.title,
                    YoutubeVideoDb.thumbnail_url: youtube_video.thumbnail_url,
                },
                where=(
                    (func.coalesce(YoutubeVideoDb.title, '') != youtube_video.title)
                    | (func.coalesce(YoutubeVideoDb.thumbnail_url, '') != youtube_video.thumbnail_url)
                ),
            )
            .returning(YoutubeVideoDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(YoutubeVideoDb.id).where(YoutubeVideoDb.video_id == youtube_video.video_id)
            )
            id_ = resp.scalar()
        youtube_video.id = id_


