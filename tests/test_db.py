import asyncio
import json
from datetime import datetime
from uuid import UUID

import pytest
from donate4fun.models import Donation, Donator, YoutubeChannel
from donate4fun.types import RequestHash
from donate4fun.db import DonationDb, Notification

from tests.test_util import verify_fixture, freeze_time


pytestmark = pytest.mark.anyio


async def test_query_donator(db_session, paid_donation_fixture):
    await db_session.save_donator(paid_donation_fixture.donator)
    await db_session.save_donator(paid_donation_fixture.donator)
    donator: Donator = await db_session.query_donator(paid_donation_fixture.donator.id)
    verify_fixture(donator, 'query-donator')


async def test_query_donation(db_session, unpaid_donation_fixture):
    donation = await db_session.query_donation(id=unpaid_donation_fixture.id)
    assert donation == unpaid_donation_fixture


@freeze_time
async def test_query_donations(db_session, paid_donation_fixture, freeze_request_hash):
    donations = await db_session.query_donations(DonationDb.paid_at.isnot(None))
    verify_fixture([donation.dict() for donation in donations], 'query-donations')


@freeze_time
async def test_create_donation(db_session):
    youtube_channel = YoutubeChannel(channel_id='q2dsaf', title='asdzxc', thumbnail_url='1wdasd')
    await db_session.save_youtube_channel(youtube_channel)
    donation = Donation(
        donator=Donator(),
        amount=100,
        youtube_channel=youtube_channel,
        r_hash=RequestHash(b'123qwe'),
    )
    donation: Donation = await db_session.create_donation(donation)
    assert donation is not None
    donation2: Donation = await db_session.query_donation(id=donation.id)
    assert donation.r_hash == donation2.r_hash


async def test_donation_paid(db_session, unpaid_donation_fixture):
    await db_session.donation_paid(donation_id=unpaid_donation_fixture.id, paid_at=datetime.utcnow(), amount=100)
    donation: Donation = await db_session.query_donation(r_hash=unpaid_donation_fixture.r_hash)
    assert donation.paid_at != None  # noqa


async def test_listen_notify(db, pubsub):
    messages = ['123', 'qwe', 'asd']
    received = []
    sent = []
    channel = 'channel'

    def callback(notification: str):
        received.append(Notification(**json.loads(notification)))

    async with pubsub.subscribe(channel, callback):
        for message in messages:
            async with db.session() as db_session:
                notification = Notification(id=UUID(int=0), status='OK', message=message)
                sent.append(notification)
                await db_session.notify(channel, notification)
        await asyncio.sleep(0.1)
    assert received == sent


async def test_db(db_session):
    db_status = await db_session.query_status()
    assert db_status == 'ok'


async def test_link_youtube_channel(db_session):
    donator = Donator(id=UUID(int=0))
    await db_session.login_donator(donator.id, 'lnauth_pub_key')
    reference_channels = []
    for i in range(3):
        youtube_channel = YoutubeChannel(
            id=UUID(int=i),
            channel_id=f"UCzxczxc{i}",
            title="channel_title",
            thumbnail_url="https://thumbnail.url/asd",
        )
        reference_channels.append(youtube_channel)
        await db_session.save_youtube_channel(youtube_channel)
        await db_session.link_youtube_channel(youtube_channel, donator)
    youtube_channels: list[YoutubeChannel] = await db_session.query_donator_youtube_channels(donator.id)
    assert youtube_channels == reference_channels
