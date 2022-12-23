from uuid import UUID
from datetime import datetime

import pytest
import sqlalchemy

from donate4fun.api import DonateRequest, DonateResponse
from donate4fun.lnd import monitor_invoices, LndClient, lnd
from donate4fun.models import Donation, YoutubeChannel, Donator, YoutubeChannelOwned
from donate4fun.types import PaymentRequest
from donate4fun.youtube import query_or_fetch_youtube_video, ChannelInfo
from donate4fun.api_youtube import GoogleAuthState

from tests.test_util import verify_response, check_response, check_notification, login_to, mark_vcr


async def test_create_donation_unsupported_youtube_url(client):
    response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://youtube.com/azxcasd').dict(),
    )
    verify_response(response, 'create-donation-unsupported_youtube_url', 400)


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate(
    client, db_session, freeze_uuids, rich_donator, settings,
):
    login_to(client, settings, rich_donator)
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/@Alex007').dict(),
    )
    verify_response(donate_response, 'donate_youtube_channel', 200)


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_video(
    client, db_session, freeze_uuids, rich_donator, settings,
):
    login_to(client, settings, rich_donator)
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/watch?v=7qH7WMzqOlU&t=692s').dict(),
    )
    verify_response(donate_response, 'donate_youtube_video', 200)


@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_cancel_donation(client, app, db, freeze_uuids, rich_donator, settings):
    login_to(client, settings, rich_donator)
    amount = 10
    donate_response = check_response(await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=amount, target='https://www.youtube.com/@Alex007').dict(),
    ))
    donation = Donation(**donate_response.json()['donation'])
    assert donation.paid_at != None  # noqa
    async with db.session() as db_session:
        me: Donator = await db_session.query_donator(id=rich_donator.id)
        assert me.balance == rich_donator.balance - amount
        youtube_channel: YoutubeChannel = await db_session.query_youtube_channel(donation.youtube_channel.id)
        assert youtube_channel.balance == amount

    cancel_response = await client.post(f"/api/v1/donation/{donation.id}/cancel")
    check_response(cancel_response)
    async with db.session() as db_session:
        donation_after_cancel: Donation = await db_session.query_donation(id=donation.id)
        assert donation_after_cancel.cancelled_at != None  # noqa
        donator: Donator = await db_session.query_donator(id=rich_donator.id)
        assert donator.balance == rich_donator.balance
        youtube_channel: YoutubeChannel = await db_session.query_youtube_channel(donation.youtube_channel.id)
        assert youtube_channel.balance == 0


async def test_cancel_donation_fail(client, app, db, freeze_uuids, rich_donator, settings):
    login_to(client, settings, rich_donator)
    amount = 10
    donate_response = check_response(await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=amount, target='https://www.youtube.com/@Alex007').dict(),
    ))
    donation = Donation(**donate_response.json()['donation'])
    async with db.session() as db_session:
        other_donator = Donator(id=UUID(int=2))
        await db_session.save_donator(other_donator)
        await db_session.transfer_youtube_donations(donation.youtube_channel, other_donator)

    cancel_response = await client.post(f"/api/v1/donation/{donation.id}/cancel")
    check_response(cancel_response, 400)
    async with db.session() as db_session:
        donation_after_cancel: Donation = await db_session.query_donation(id=donation.id)
        assert donation_after_cancel.cancelled_at == None  # noqa
        new_rich_donator: Donator = await db_session.query_donator(id=rich_donator.id)
        assert new_rich_donator.balance == rich_donator.balance - amount
        youtube_channel: YoutubeChannel = await db_session.query_youtube_channel(donation.youtube_channel.id)
        assert youtube_channel.balance == 0


async def test_donate_full(
    client, app, freeze_uuids, payer_lnd: LndClient, freeze_request_hash_json, db,
):
    video_id = 'rq2SVMXEMPI'
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=20, target=f'https://www.youtube.com/watch?v={video_id}').dict(),
    )
    check_response(donate_response, 200)
    donation_id = donate_response.json()['donation']['id']
    assert donation_id == str(UUID(int=1))
    payment_request = PaymentRequest(donate_response.json()['payment_request'])
    check_donation_notification = check_notification(client, 'donation', donation_id)
    check_video_notification = check_notification(client, 'youtube-video-by-vid', video_id)
    async with monitor_invoices(lnd, db), check_donation_notification, check_video_notification:
        await payer_lnd.pay_invoice(payment_request)
    donation_response = await client.get(f"/api/v1/donation/{donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa


async def test_transfer_from_youtube(client, db, paid_donation_fixture, registered_donator, settings):
    login_to(client, settings, registered_donator)
    channel_id = paid_donation_fixture.youtube_channel.id
    # Update balance to target value
    async with db.session() as db_session:
        await db_session.link_youtube_channel(
            donator=registered_donator, youtube_channel=paid_donation_fixture.youtube_channel, via_oauth=False,
        )

    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    check_response(resp, 200)
    amount = resp.json()['amount']
    assert amount == paid_donation_fixture.amount
    async with db.session() as db_session:
        channel = await db_session.query_youtube_channel(youtube_channel_id=channel_id, owner_id=registered_donator.id)
        assert channel.balance == 0
        donator = await db_session.query_donator(id=registered_donator.id)
        assert donator.balance == amount
        donation = await db_session.query_donation(id=paid_donation_fixture.id)
        assert donation.claimed_at != None  # noqa


async def test_transfer_from_youtube_not_linked(client, db, paid_donation_fixture):
    channel_id = paid_donation_fixture.youtube_channel.id
    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    verify_response(resp, 'transfer-from-youtube-not-linked', 401)


async def test_transfer_from_youtube_not_connected(client, db, paid_donation_fixture):
    donator = Donator(id=UUID(int=0))
    channel_id = paid_donation_fixture.youtube_channel.id
    # Update balance to target value
    async with db.session() as db_session:
        await db_session.link_youtube_channel(
            donator=donator, youtube_channel=paid_donation_fixture.youtube_channel, via_oauth=False,
        )

    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    verify_response(resp, 'transfer-from-youtube-not-connected', 400)


async def test_youtube_video(client):
    youtube_videoid = 'sLcdanDHPjM'
    origin = 'https://youtube.com'
    response = await client.get(f"/api/v1/youtube/video/{youtube_videoid}", headers=dict(origin=origin))
    verify_response(response, 'youtube-video', 200)


async def test_youtube_video_no_cors(client):
    youtube_videoid = 'sLcdanDHPjM'
    response = await client.get(f"/api/v1/youtube/video/{youtube_videoid}", headers=dict(origin="https://unallowed.com"))
    check_response(response, 200)
    assert 'Access-Control-Allow-Origin' not in response.headers


async def test_donate_from_balance(
    client, app, freeze_uuids, rich_donator, settings,
):
    login_to(client, settings, rich_donator)
    video_id = 'rq2SVMXEMPI'
    amount = 30
    donation_id = UUID(int=1)
    check_donation_notification = check_notification(client, 'donation', donation_id)
    check_video_notification = check_notification(client, 'youtube-video-by-vid', video_id)
    async with check_donation_notification, check_video_notification:
        donate_response: DonateResponse = await client.post(
            "/api/v1/donate",
            json=DonateRequest(amount=amount, target=f'https://www.youtube.com/watch?v={video_id}').dict(),
        )
        check_response(donate_response, 200)
        donation = donate_response.json()['donation']
        assert donation['id'] == str(donation_id)
        assert donation['r_hash'] == None  # noqa
    donation_response = await client.get(f"/api/v1/donation/{donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa
    me_response = await client.get('/api/v1/donator/me')
    check_response(me_response, 200)
    assert me_response.json()['donator']['balance'] == rich_donator.balance - amount


async def test_link_youtube_channel(db_session):
    donator = Donator(id=UUID(int=0))
    reference_channels = []
    for i in range(3):
        youtube_channel = YoutubeChannelOwned(
            id=UUID(int=i),
            channel_id=f"UCzxczxc{i}",
            title="channel_title",
            thumbnail_url="https://thumbnail.url/asd",
            via_oauth=False,
        )
        reference_channels.append(youtube_channel)
        await db_session.save_youtube_channel(youtube_channel)
        await db_session.link_youtube_channel(youtube_channel, donator, via_oauth=False)
    youtube_channels: list[YoutubeChannelOwned] = await db_session.query_donator_youtube_channels(donator.id)
    assert youtube_channels == reference_channels
    channel: YoutubeChannelOwned = await db_session.query_youtube_channel(
        youtube_channel_id=reference_channels[0].id, owner_id=UUID(int=0)
    )
    assert channel.owner_id == donator.id
    channel: YoutubeChannelOwned = await db_session.query_youtube_channel(
        youtube_channel_id=reference_channels[0].id, owner_id=UUID(int=1)
    )
    assert not channel.owner_id == donator.id


async def test_link_youtube_channel_via_oauth(db_session):
    donator = Donator(id=UUID(int=0))
    youtube_channel = YoutubeChannel(
        id=UUID(int=0),
        channel_id="UCzxczxc",
        title="channel_title",
        thumbnail_url="https://thumbnail.url/asd",
    )
    await db_session.save_youtube_channel(youtube_channel)
    await db_session.link_youtube_channel(youtube_channel, donator, via_oauth=True)
    donator = await db_session.query_donator(donator.id)
    assert donator.connected == True  # noqa

    # Test that after relinking without OAuth donator is still connected
    await db_session.link_youtube_channel(youtube_channel, donator, via_oauth=False)
    donator = await db_session.query_donator(donator.id)
    assert donator.connected == True  # noqa

    # Test that multiple donators could not be linked using one channel
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await db_session.link_youtube_channel(youtube_channel, Donator(id=UUID(int=1)), via_oauth=True)


async def test_unlink_youtube_channel(db_session):
    donator = Donator(id=UUID(int=0))
    youtube_channel = YoutubeChannel(
        id=UUID(int=0),
        channel_id="UCzxczxc",
        title="channel_title",
        thumbnail_url="https://thumbnail.url/asd",
    )
    await db_session.save_youtube_channel(youtube_channel)
    await db_session.link_youtube_channel(youtube_channel, donator, via_oauth=True)
    await db_session.unlink_youtube_channel(channel_id=youtube_channel.id, owner_id=donator.id)
    donator = await db_session.query_donator(donator.id)
    assert donator.connected == False  # noqa


async def test_unlink_youtube_channel_with_balance(db, client, settings, monkeypatch):
    donator = Donator(id=UUID(int=0), balance=100)
    async with db.session() as db_session:
        await db_session.save_donator(donator)
        youtube_channel = YoutubeChannel(
            id=UUID(int=0),
            channel_id="UCzxczxc",
            title="channel_title",
            thumbnail_url="https://thumbnail.url/asd",
            last_fetched_at=datetime.utcnow(),
        )
        await db_session.save_youtube_channel(youtube_channel)
        await db_session.link_youtube_channel(youtube_channel, donator, via_oauth=True)
        youtube_channel2 = YoutubeChannel(
            id=UUID(int=1),
            channel_id="UCzxczxd",
            title="channel_title",
            thumbnail_url="https://thumbnail.url/asd",
        )
        await db_session.save_youtube_channel(youtube_channel2)
        await db_session.link_youtube_channel(youtube_channel2, donator, via_oauth=True)

    login_to(client, settings, donator)
    check_response(await client.post(f'/api/v1/youtube/channel/{youtube_channel.id}/unlink'))
    check_response(await client.post(f'/api/v1/youtube/channel/{youtube_channel2.id}/unlink'), 400)

    # Test unlink with lnauth_pubkey
    async with db.session() as db_session:
        donator.lnauth_pubkey = 'pubkey'
        await db_session.save_donator(donator)
    check_response(await client.post(f'/api/v1/youtube/channel/{youtube_channel2.id}/unlink'))

    # Test that lnauth_pubkey is not changed after link
    async def patched_fetch_user_channel(request, code):
        return ChannelInfo(id=youtube_channel.channel_id, title='title', description='descr')
    monkeypatch.setattr('donate4fun.api_youtube.fetch_user_channel', patched_fetch_user_channel)
    check_response(await client.get(
        '/api/v1/youtube/auth-redirect',
        params=dict(state=GoogleAuthState(donator_id=donator.id, last_url='http://a.com').to_jwt(), code=123),
    ), 307)
    async with db.session() as db_session:
        new_donator: Donator = await db_session.query_donator(donator.id)
    assert new_donator.lnauth_pubkey == donator.lnauth_pubkey


@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_login_via_oauth(client, settings, monkeypatch, db, freeze_uuids):
    info = ChannelInfo(id='UCxxx', title='title', description='descr')

    async def patched_fetch_user_channel(request, code):
        return info
    monkeypatch.setattr('donate4fun.api_youtube.fetch_user_channel', patched_fetch_user_channel)
    async with db.session() as db_session:
        channel = YoutubeChannel(
            channel_id=info.id,
            title=info.title,
            description=info.description,
            last_fetched_at=datetime.utcnow(),
        )
        await db_session.save_youtube_channel(channel)
    donator = Donator(id=UUID(int=0))
    login_to(client, settings, donator)
    response = await client.get(
        '/api/v1/youtube/auth-redirect',
        params=dict(state=GoogleAuthState(donator_id=donator.id, last_url='http://a.com').to_jwt(), code=123),
    )
    check_response(response, 307)
    me = Donator(**check_response(await client.get('/api/v1/me')).json())
    assert me.id == donator.id
    assert me.connected == True  # noqa

    # Try to relogin from other account to the first account
    other_donator = Donator(id=UUID(int=1))
    login_to(client, settings, other_donator)
    response = await client.get(
        '/api/v1/youtube/auth-redirect',
        params=dict(state=GoogleAuthState(donator_id=other_donator.id, last_url='http://a.com').to_jwt(), code=123),
    )
    check_response(response, 307)
    me = Donator(**check_response(await client.get('/api/v1/me')).json())
    assert me.id == donator.id
    assert me.connected == True  # noqa

    # Test channel API
    verify_response(await client.get(f'/api/v1/youtube/channel/{channel.id}'), 'youtube-channel-owned')


@mark_vcr
@pytest.mark.parametrize('video_id', ['VOG-fFhq7kk', 'tOu3f-j4ukY'])
async def test_query_or_fetch_youtube_video(db_session, video_id):
    """
    One channel has banner, other not
    """
    await query_or_fetch_youtube_video(video_id='VOG-fFhq7kk', db=db_session)
