from uuid import uuid4
from datetime import datetime

import pytest
import anyio
from donate4fun.models import Donation

from tests.test_util import verify_fixture


pytestmark = pytest.mark.anyio


async def test_query_donator(db_session):
    donator = await db_session.query_donator('9842425d-f653-4758-9afc-40a576561597')
    assert len(donator.donations) == 2
    for donation in donator.donations:
        assert donation.donator is donator
        assert donation.youtube_channel.title == 'Alex007SC2'


async def test_query_donatee(db_session):
    donations = await db_session.query_donatee('120108f4-a5e3-492f-8a4b-fdaff6dbfaf0')
    assert len(donations) == 3
    verify_fixture([donation.dict() for donation in donations], 'query-donatee')


async def test_query_donation(db_session):
    donation = await db_session.query_donation(id='ccca65f0-9e47-4858-a113-b080f352f996')
    assert donation is not None


async def test_query_donations(db_session):
    donations = await db_session.query_recent_donations()
    assert len(donations) == 2
    verify_fixture([donation.dict() for donation in donations], 'query-donations')


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


async def test_donation_paid(db_session):
    await db_session.donation_paid(r_hash='asdas', paid_at=datetime.utcnow(), amount=100)
    donation: Donation = await db_session.query_donation(r_hash='asdas')
    assert donation is not None


async def test_listen_notify(db_session):
    messages = ['123', 'qwe']
    channel = 'channel'

    async def listen(task_status):
        i = 0
        async for msg in db_session.listen(channel):
            if msg is None:
                task_status.started()
                continue
            assert messages[i] == msg
            i += 1

    async with anyio.create_task_group() as tg:
        await tg.start(listen)
        for msg in messages:
            await db_session.notify(channel, msg)
        tg.cancel_scope.cancel()

    async with anyio.create_task_group() as tg:
        await tg.start(listen)
        for msg in messages:
            await db_session.notify(channel, msg)
        tg.cancel_scope.cancel()
