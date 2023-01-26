import asyncio
import json
from datetime import datetime
from uuid import UUID

import pytest
from donate4fun.models import Donation, Donator, YoutubeChannel
from donate4fun.types import RequestHash
from donate4fun.db_models import DonationDb
from donate4fun.db import Notification
from donate4fun.db_youtube import YoutubeDbLib
from donate4fun.db_donations import DonationsDbLib

from tests.test_util import verify_fixture, freeze_time


pytestmark = pytest.mark.anyio


async def test_query_donator(db_session, paid_donation_fixture):
    await db_session.save_donator(paid_donation_fixture.donator)
    await db_session.save_donator(paid_donation_fixture.donator)
    donator: Donator = await db_session.query_donator(id=paid_donation_fixture.donator.id)
    verify_fixture(donator, 'query-donator')


async def test_query_donation(db_session, unpaid_donation_fixture):
    donation = await DonationsDbLib(db_session).query_donation(id=unpaid_donation_fixture.id)
    assert donation == unpaid_donation_fixture


@freeze_time
async def test_query_donations(db_session, paid_donation_fixture, freeze_request_hash):
    donations = await DonationsDbLib(db_session).query_donations(DonationDb.paid_at.isnot(None))
    verify_fixture([donation.dict() for donation in donations], 'query-donations')


@freeze_time
async def test_create_donation(db_session):
    youtube_channel = YoutubeChannel(channel_id='q2dsaf', title='asdzxc', thumbnail_url='http://example.com/thumbnail')
    await YoutubeDbLib(db_session).save_account(youtube_channel)
    donation = Donation(
        donator=Donator(),
        amount=100,
        youtube_channel=youtube_channel,
        r_hash=RequestHash(b'123qwe'),
    )
    donations_db = DonationsDbLib(db_session)
    donation: Donation = await donations_db.create_donation(donation)
    assert donation is not None
    donation2: Donation = await donations_db.query_donation(id=donation.id)
    assert donation.r_hash == donation2.r_hash


async def test_donation_paid(db_session, unpaid_donation_fixture):
    donations_db = DonationsDbLib(db_session)
    await donations_db.donation_paid(donation_id=unpaid_donation_fixture.id, paid_at=datetime.utcnow(), amount=100)
    donation: Donation = await donations_db.lock_donation(r_hash=unpaid_donation_fixture.r_hash)
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
