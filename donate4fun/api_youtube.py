import logging
from uuid import UUID

import posthog
from fastapi import Depends, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from aiogoogle import Aiogoogle
from pydantic import AnyHttpUrl
from sqlalchemy.orm.exc import NoResultFound

from .api_utils import get_donator, load_donator, get_db_session
from .models import BaseModel, YoutubeVideo, YoutubeChannel, Donator, YoutubeChannelOwned, Donation, TransferResponse
from .youtube import (
    find_comment, query_or_fetch_youtube_channel, ChannelInfo, fetch_user_channel,
)
from .db_models import DonationDb
from .settings import settings
from .types import ValidationError


router = APIRouter(prefix='/youtube')
legacy_router = APIRouter()
logger = logging.getLogger(__name__)


class YoutubeVideoResponse(BaseModel):
    id: UUID | None
    total_donated: int


@legacy_router.get('/youtube-video/{video_id}', response_model=YoutubeVideoResponse)
@router.get('/video/{video_id}', response_model=YoutubeVideoResponse)
async def youtube_video_info(video_id: str, db=Depends(get_db_session)):
    try:
        video: YoutubeVideo = await db.query_youtube_video(video_id=video_id)
        return YoutubeVideoResponse(id=video.id, total_donated=video.total_donated)
    except NoResultFound:
        return YoutubeVideoResponse(id=None, total_donated=0)


class OwnershipMessage(BaseModel):
    message: str


@router.get('/ownership-message', response_model=OwnershipMessage)
async def ownership_message(donator=Depends(get_donator)):
    return OwnershipMessage(message=settings.ownership_message.format(donator_id=donator.id))


@router.post('/check-ownership', response_model=list[YoutubeChannel])
async def ownership_check(donator=Depends(get_donator), db=Depends(get_db_session)):
    channel_ids = await find_comment(
        video_id='J2Tz2jGQjHE',
        comment=settings.ownership_message.format(donator_id=donator.id),
    )
    channels = []
    for channel_id in channel_ids:
        youtube_channel: YoutubeChannel = await query_or_fetch_youtube_channel(channel_id, db)
        is_new = await db.link_youtube_channel(youtube_channel, donator, via_oauth=False)
        if is_new:
            channels.append(youtube_channel)
    return channels


class GoogleAuthState(BaseModel):
    last_url: AnyHttpUrl
    donator_id: UUID


@router.get('/oauth', response_class=JSONResponse)
async def login_via_google(request: Request, donator=Depends(get_donator)):
    aiogoogle = Aiogoogle()
    url = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=f'{settings.base_url}/api/v1/youtube/auth-redirect',
            **settings.youtube.oauth.dict(),
        ),
        state=GoogleAuthState(last_url=request.headers['referer'], donator_id=donator.id).to_jwt(),
    )
    return dict(url=url)


@router.get('/auth-redirect')
async def auth_google(
    request: Request, state: str, error: str = None, error_description: str = None, code: str = None,
    db_session=Depends(get_db_session), donator=Depends(get_donator),
):
    auth_state = GoogleAuthState.from_jwt(state)
    if auth_state.donator_id != donator.id:
        raise ValidationError(
            f"User that initiated Google Auth {donator.id} is not the current user {auth_state.donator_id}, rejecting auth"
        )
    if error:
        return {
            'error': error,
            'error_description': error_description
        }
    elif code:
        try:
            channel_info: ChannelInfo = await fetch_user_channel(request, code)
        except Exception:
            logger.exception("Failed to fetch user's channel")
            # TODO: add exception info to last_url hash param and show it using toast
            return RedirectResponse(auth_state.last_url)
        else:
            channel: YoutubeChannel = await query_or_fetch_youtube_channel(channel_info.id, db_session)
            owned_channel: YoutubeChannelOwned = await db_session.query_youtube_channel(channel.id)
            if owned_channel.via_oauth:
                request.session['donator'] = str(owned_channel.owner_id)
            else:
                await db_session.link_youtube_channel(channel, donator, via_oauth=True)
            request.session['connected'] = True
            return RedirectResponse(f'/youtube/{channel.id}/owner')
    else:
        # Should either receive a code or an error
        raise Exception("Something's probably wrong with your callback")


class YoutubeChannelResponse(YoutubeChannel):
    is_my: bool


@router.get("/channel/{channel_id}", response_model=YoutubeChannelResponse)
async def youtube_channel(channel_id: UUID, db=Depends(get_db_session), me=Depends(get_donator)):
    channel: YoutubeChannelOwned = await db.query_youtube_channel(channel_id, owner_id=me.id)
    return YoutubeChannelResponse(
        **channel.dict(),
        is_my=channel.owner_id == me.id,
    )


@router.post('/channel/{channel_id}/transfer', response_model=TransferResponse)
async def youtube_channel_transfer(channel_id: UUID, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    channel: YoutubeChannelOwned = await db.query_youtube_channel(channel_id, donator.id)
    if channel.owner_id != donator.id:
        raise HTTPException(status_code=401, detail="You should prove that you own YouTube channel")
    if not donator.connected:
        raise ValidationError("You should have a connected auth method to claim donations")
    if channel.balance != 0:
        amount = await db.transfer_youtube_donations(youtube_channel=channel, donator=donator)
    posthog.capture(donator.id, 'transfer', dict(amount=amount, source='youtube'))
    return TransferResponse(amount=amount)


@router.get("/linked", response_model=list[YoutubeChannelOwned])
async def my_linked_youtube_channels(db=Depends(get_db_session), me=Depends(get_donator)):
    return await db.query_donator_youtube_channels(me.id)


@router.get("/channel/{channel_id}/donations/by-donatee", response_model=list[Donation])
async def donatee_donations(channel_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations((DonationDb.youtube_channel_id == channel_id) & DonationDb.paid_at.isnot(None))


@router.post("/channel/{channel_id}/unlink")
async def unlink_youtube_channel(channel_id: UUID, db=Depends(get_db_session), me: Donator = Depends(get_donator)):
    await db.unlink_youtube_channel(channel_id=channel_id, owner_id=me.id)
    me = await db.query_donator(id=me.id)
    if not me.connected and me.balance > 0:
        raise ValidationError("Unable to unlink last auth method having a positive balance")
