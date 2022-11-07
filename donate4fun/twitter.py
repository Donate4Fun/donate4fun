from dataclasses import dataclass

import httpx

from .db import DbSession, NoResultFound
from .models import Donation, TwitterAuthor, TwitterTweet
from .types import ValidationError
from .settings import settings


@dataclass
class TwitterDonatee:
    author_handle: str
    tweet_id: str | None = None

    async def fetch(self, donation: Donation, db: DbSession):
        if self.tweet_id:
            tweet = TwitterTweet(tweet_id=self.tweet_id)
            await db.get_or_create_tweet(tweet)
            donation.twitter_tweet = tweet
        donation.twitter_author = await query_or_fetch_twitter_author(db=db, handle=self.author_handle)


class UnsupportedTwitterUrl(ValidationError):
    pass


def validate_twitter_url(parsed) -> TwitterDonatee:
    parts = parsed.path.split('/')
    if len(parts) == 2:
        return TwitterDonatee(author_handle=parts[1])
    elif len(parts) == 4 and parts[2] == 'status':
        return TwitterDonatee(tweet_id=int(parts[3]), author_handle=parts[1])
    else:
        raise UnsupportedTwitterUrl


async def query_or_fetch_twitter_author(db: DbSession, handle: str) -> TwitterAuthor:
    try:
        author: TwitterAuthor = await db.query_twitter_author(handle=handle)
    except NoResultFound:
        author: TwitterAuthor = await fetch_twitter_author(handle)
        await db.save_twitter_author(author)
    return author


async def fetch_twitter_author(handle: str) -> TwitterAuthor:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://api.twitter.com/2/users/by/username/{handle}',
            params={'user.fields': 'id,name,profile_image_url'},
            headers=dict(Authorization=f'Bearer {settings.twitter.bearer_token}'),
        )
        response.raise_for_status()
        data = response.json()['data']
        return TwitterAuthor(
            user_id=int(data['id']),
            handle=data['username'],
            name=data['name'],
            profile_image_url=data['profile_image_url'],
        )
