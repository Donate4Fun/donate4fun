import unicodedata
from uuid import uuid4, UUID

import posthog
from furl import furl
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm.exc import NoResultFound  # noqa - imported from other modules

from .models import Donator, Credentials, Donation, YoutubeChannelOwned, TwitterAccountOwned
from .db import DbSession, db
from .core import ContextualObject
from .types import LightningAddress
from .settings import settings


task_group = ContextualObject('task_group')


def get_donator(request: Request):
    creds = Credentials(**request.session)
    if creds.donator is not None:
        donator = Donator(id=creds.donator, lnauth_pubkey=creds.lnauth_pubkey)
    else:
        donator = Donator(id=uuid4())
        creds.donator = donator.id
    request.session.update(**creds.to_json_dict())
    return donator


def only_me(request: Request, donator_id: UUID, me=Depends(get_donator)):
    if donator_id != me.id:
        raise HTTPException(status_code=403, detail="This API available only to the owner")
    return me


async def load_donator(db: DbSession, donator_id: UUID) -> Donator:
    try:
        return await db.query_donator(donator_id)
    except NoResultFound:
        return Donator(id=donator_id)


async def get_db_session():
    async with db.session() as session:
        yield session


def scrape_lightning_address(text: str):
    # Remove Mark characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'M')
    return LightningAddress.parse(text)


def track_donation(donation: Donation):
    if donation.twitter_account:
        target_type = 'twitter'
    elif donation.youtube_channel:
        target_type = 'youtube'
    elif donation.receiver:
        target_type = 'donate4fun'
    else:
        target_type = 'unknown'
    if donation.lightning_address:
        via = 'lightning-address'
    else:
        via = 'donate4fun'
    donator_id = donation.donator and donation.donator.id
    posthog.capture(donator_id, 'donation-paid', dict(amount=donation.amount, target_type=target_type, via=via))


def make_absolute_uri(path: str) -> str:
    return str(furl(url=settings.base_url, path=furl(path).path))


async def auto_transfer_donations(db: DbSession, donation: Donation):
    if donation.youtube_channel:
        if not isinstance(donation.youtube_channel, YoutubeChannelOwned):
            donation.youtube_channel = await db.query_youtube_channel(id=donation.youtube_channel.id)
        if donation.youtube_channel.owner_id is not None:
            await db.transfer_youtube_donations(donation.youtube_channel, Donator(id=donation.youtube_channel.owner_id))
    elif donation.twitter_account:
        if not isinstance(donation.twitter_account, TwitterAccountOwned):
            donation.twitter_account = await db.query_twitter_account(id=donation.twitter_account.id)
        if donation.twitter_account.owner_id is not None:
            await db.transfer_twitter_donations(donation.twitter_account, Donator(id=donation.twitter_account.owner_id))
