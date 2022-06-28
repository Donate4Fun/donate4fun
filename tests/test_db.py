from datetime import datetime
from uuid import UUID

import pytest
from donate4fun.models import Donation, Donator, YoutubeChannel
from donate4fun.types import RequestHash
from donate4fun.db import DonationDb, Notification

from tests.test_util import verify_fixture


pytestmark = pytest.mark.anyio


async def test_query_donator(db_session, paid_donation_fixture):
    await db_session.save_donator(paid_donation_fixture.donator)
    await db_session.save_donator(paid_donation_fixture.donator)
    donator: Donator = await db_session.query_donator(paid_donation_fixture.donator.id)
    verify_fixture(donator, 'query-donator')


async def test_query_donation(db_session, unpaid_donation_fixture):
    donation = await db_session.query_donation(id=unpaid_donation_fixture.id)
    assert donation == unpaid_donation_fixture


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_query_donations(db_session, paid_donation_fixture, freeze_request_hash):
    donations = await db_session.query_donations(DonationDb.paid_at.isnot(None))
    verify_fixture([donation.dict() for donation in donations], 'query-donations')


@pytest.mark.freeze_time('2022-02-02 22:22:22')
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
    await db_session.donation_paid(r_hash=unpaid_donation_fixture.r_hash, paid_at=datetime.utcnow(), amount=100)
    donation: Donation = await db_session.query_donation(r_hash=unpaid_donation_fixture.r_hash)
    assert donation.paid_at != None  # noqa


async def test_listen_notify(db):
    messages = ['123', 'qwe', 'asd']
    channel = 'channel'

    i = 0
    async with db.pubsub() as sub:
        async for received in sub.listen(channel):
            if received is not None:
                assert received.message == messages[i - 1]
            if i == len(messages):
                break
            async with db.pubsub() as pub:
                await pub.notify(channel, Notification(id=UUID(int=0), status='OK', message=messages[i]))
            i += 1


async def test_db(db_session):
    db_status = await db_session.query_status()
    assert db_status == 'ok'
