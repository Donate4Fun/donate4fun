from uuid import UUID
from datetime import datetime, timedelta

import anyio
import pytest

from donate4fun.api import DonateRequest, DonateResponse
from donate4fun.lnd import monitor_invoices, LndClient
from donate4fun.models import Donation, YoutubeChannel, Donator, YoutubeChannelOwned
from donate4fun.youtube import query_or_fetch_youtube_video

from tests.test_util import verify_fixture, verify_response, check_response, freeze_time, check_notification, login_to, mark_vcr


async def test_create_donation_unsupported_youtube_url(client):
    response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://youtube.com/azxcasd').dict(),
    )
    verify_response(response, 'create-donation-unsupported_youtube_url', 400)


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    verify_response(donate_response, 'donate_youtube_channel', 200)


@mark_vcr
@pytest.mark.freeze_time('2022-02-02 22:22:22')
async def test_donate_video(
    client, db_session, freeze_uuids, freeze_request_hash, freeze_payment_request,
):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=100, target='https://www.youtube.com/watch?v=7qH7WMzqOlU&t=692s').dict(),
    )
    verify_response(donate_response, 'donate_youtube_video', 200)


@mark_vcr
@pytest.mark.skip(reason="Only HODL invoices (not implemented)")
@pytest.mark.freeze_time('2022-02-02T22:22:22')
async def test_cancel_donation(client, app, db_session, freeze_uuids):
    donate_response = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=10, target='https://www.youtube.com/c/Alex007SC2').dict(),
    )
    donation_id = donate_response.json()['id']
    async with anyio.create_task_group() as tg, client.ws_session(f"/api/v1/donation/{donation_id}/subscribe") as ws:
        await tg.start(monitor_invoices, app.lnd, app.db)
        cancel_response = await client.post(f"/api/v1/donation/{donation_id}/cancel")
        verify_response(cancel_response, "cancel-donation-cancel-response")
        ws_response = []
        while True:
            resp = await ws.receive_json()
            ws_response.append(resp)
        verify_fixture(ws_response, "cancel-donation-subscribe")


async def test_donate_full(
    client, app, freeze_uuids, payer_lnd: LndClient, freeze_request_hash_json, pubsub,
):
    video_id = 'rq2SVMXEMPI'
    donate_response: DonateResponse = await client.post(
        "/api/v1/donate",
        json=DonateRequest(amount=20, target=f'https://www.youtube.com/watch?v={video_id}').dict(),
    )
    check_response(donate_response, 200)
    donation_id = donate_response.json()['donation']['id']
    assert donation_id == str(UUID(int=1))
    payment_request = donate_response.json()['payment_request']
    check_donation_notification = check_notification(client, 'donation', donation_id)
    check_video_notification = check_notification(client, 'youtube-video-by-vid', video_id)
    async with monitor_invoices(app.lnd, app.db), check_donation_notification, check_video_notification:
        await payer_lnd.pay_invoice(payment_request)
    donation_response = await client.get(f"/api/v1/donation/{donation_id}")
    check_response(donation_response, 200)
    assert donation_response.json()['donation']['paid_at'] != None  # noqa


async def test_transfer_from_youtube(client, db, paid_donation_fixture, registered_donator, client_session, settings):
    login_to(client, settings, registered_donator)
    channel_id = paid_donation_fixture.youtube_channel.id
    # Update balance to target value
    async with db.session() as db_session:
        await db_session.link_youtube_channel(
            donator=registered_donator, youtube_channel=paid_donation_fixture.youtube_channel,
        )

    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    check_response(resp, 200)
    amount = resp.json()['amount']
    assert amount == paid_donation_fixture.amount
    async with db.session() as db_session:
        channel = await db_session.query_youtube_channel(youtube_channel_id=channel_id, owner_id=registered_donator.id)
        assert channel.balance == 0
        donator = await db_session.query_donator(donator_id=registered_donator.id)
        assert donator.balance == amount


async def test_transfer_from_youtube_not_linked(client, db, paid_donation_fixture, client_session):
    channel_id = paid_donation_fixture.youtube_channel.id
    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    verify_response(resp, 'transfer-from-youtube-not-linked', 401)


async def test_transfer_from_youtube_not_connected(client, db, paid_donation_fixture, client_session):
    channel_id = paid_donation_fixture.youtube_channel.id
    # Update balance to target value
    async with db.session() as db_session:
        await db_session.link_youtube_channel(
            donator=Donator(id=client_session.donator), youtube_channel=paid_donation_fixture.youtube_channel,
        )

    resp = await client.post(f'/api/v1/youtube/channel/{channel_id}/transfer')
    verify_response(resp, 'transfer-from-youtube-not-connected', 400)


async def test_youtube_video(client):
    youtube_videoid = 'sLcdanDHPjM'
    origin = 'https://youtube.com'
    response = await client.get(f"/api/v1/youtube/video/{youtube_videoid}", headers=dict(origin=origin))
    verify_response(response, 'youtube-video', 200)
    assert response.headers['access-control-allow-origin'] == origin


async def test_youtube_video_no_cors(client):
    youtube_videoid = 'sLcdanDHPjM'
    response = await client.get(f"/api/v1/youtube/video/{youtube_videoid}", headers=dict(origin="https://unallowed.com"))
    check_response(response, 200)
    assert 'Access-Control-Allow-Origin' not in response.headers


async def test_donate_from_balance(
    client, app, freeze_uuids, pubsub, rich_donator, settings,
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


async def donate(
    db_session, donator: Donator, youtube_channel: YoutubeChannel, amount: int, donation_id: UUID, paid_at: datetime,
):
    donation: Donation = Donation(
        id=donation_id,
        donator=donator,
        amount=amount,
        youtube_channel=youtube_channel,
    )
    await db_session.create_donation(donation)
    await db_session.donation_paid(
        donation_id=donation.id,
        amount=donation.amount,
        paid_at=paid_at,
    )


@freeze_time
async def test_recent_donatees(client, db, paid_donation_fixture, rich_donator, freeze_request_hash_json):
    async with db.session() as db_session:
        youtube_channel = YoutubeChannel(
            id=UUID(int=2), channel_id='0001', title='0001', thumbnail_url='http://0001/img',
        )
        await db_session.save_youtube_channel(youtube_channel)
        await donate(db_session, rich_donator, youtube_channel, 20, UUID(int=2), datetime.now())
        await donate(db_session, rich_donator, youtube_channel, 30, UUID(int=3), datetime.now())
        await donate(db_session, rich_donator, youtube_channel, 40, UUID(int=4), datetime.now() - timedelta(days=1, minutes=1))

    response = await client.get("/api/v1/donatee/recently-donated")
    verify_response(response, 'recently-donated-donatees', 200)


def login_youtuber(client, client_session, youtube_channel):
    client_session.youtube_channels = [youtube_channel.id]
    client.cookies['session'] = client_session.to_jwt()


async def test_link_youtube_channel(db_session):
    donator = Donator(id=UUID(int=0))
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
    channel: YoutubeChannelOwned = await db_session.query_youtube_channel(
        youtube_channel_id=reference_channels[0].id, owner_id=UUID(int=0)
    )
    assert channel.is_my
    channel: YoutubeChannelOwned = await db_session.query_youtube_channel(
        youtube_channel_id=reference_channels[0].id, owner_id=UUID(int=1)
    )
    assert not channel.is_my


@mark_vcr
@pytest.mark.parametrize('video_id', ['VOG-fFhq7kk', 'tOu3f-j4ukY'])
async def test_query_or_fetch_youtube_video(db_session, video_id):
    """
    One channel has banner, other not
    """
    await query_or_fetch_youtube_video(video_id='VOG-fFhq7kk', db=db_session)
