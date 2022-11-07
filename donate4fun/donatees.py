import re
from urllib.parse import urlparse

from email_validator import validate_email

from .youtube import validate_youtube_url
from .twitter import validate_twitter_url
from .models import Donation
from .db import DbSession
from .types import UnsupportedTarget, Url


async def validate_target(target: str):
    if re.match(r'https?://.+', target):
        return await validate_target_url(target)
    return validate_email(target).email


async def validate_target_url(target: Url):
    parsed = urlparse(target)
    if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be']:
        return validate_youtube_url(parsed)
    elif parsed.hostname in ['twitter.com', 'www.twitter.com']:
        return validate_twitter_url(parsed)
    else:
        raise UnsupportedTarget("URL is invalid")


async def apply_target(donation: Donation, target: str, db: DbSession):
    donatee = await validate_target(target)
    await donatee.fetch(donation, db)
