from uuid import uuid4
from datetime import datetime

import pytest
from donate4fun.models import Donation

from tests.test_util import verify_fixture


pytestmark = pytest.mark.anyio


@pytest.mark.skip("no api to update or create donator yet")
async def test_query_donator(db_session):
    donator = await db_session.query_donator('9842425d-f653-4758-9afc-40a576561597')
    assert len(donator.donations) == 2
    for donation in donator.donations:
        assert donation.donator is donator
        assert donation.youtube_channel.title == 'Alex007SC2'


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_query_donatee(db_session, donation_fixture: Donation):
    donations: list[Donation] = await db_session.query_donatee(donation_fixture.youtube_channel.id)
    verify_fixture([donation.dict() for donation in donations], 'query-donatee')


async def test_query_donation(db_session, donation_fixture):
    donation = await db_session.query_donation(id=donation_fixture.id)
    assert donation == donation_fixture


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_query_donations(db_session, paid_donation_fixture):
    donations = await db_session.query_recent_donations()
    verify_fixture([donation.dict() for donation in donations], 'query-donations')


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_create_donation(db_session):
    youtube_channel_id = await db_session.get_or_create_youtube_channel(
        channel_id='q2dsaf', title='asdzxc', thumbnail_url='1wdasd',
    )
    donation: Donation = await db_session.create_donation(
        donator_id=uuid4(),
        amount=100,
        youtube_channel_id=youtube_channel_id,
        r_hash='hash',
    )
    assert donation is not None
    donation2: Donation = await db_session.query_donation(id=donation.id)
    assert donation.r_hash == donation2.r_hash


async def test_donation_paid(db_session, donation_fixture):
    await db_session.donation_paid(r_hash=donation_fixture.r_hash, paid_at=datetime.utcnow(), amount=100)
    donation: Donation = await db_session.query_donation(r_hash=donation_fixture.r_hash)
    assert donation.paid_at != None  # noqa


async def test_listen_notify(db):
    messages = ['123', 'qwe', 'asd']
    channel = 'channel'

    i = 0
    async with db.pubsub() as sub:
        async for received in sub.listen(channel):
            if received is not None:
                assert received == messages[i - 1]
            if i == len(messages):
                break
            async with db.pubsub() as pub:
                await pub.notify(channel, messages[i])
            i += 1
