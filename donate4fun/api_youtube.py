import logging
from uuid import UUID

from fastapi import Depends, APIRouter, Request
from aiogoogle import Aiogoogle
from sqlalchemy.orm.exc import NoResultFound

from .api_utils import get_donator, get_db_session, make_absolute_uri
from .models import (
    BaseModel, YoutubeVideo, YoutubeChannel, Donator, YoutubeChannelOwned, OAuthState,
    OAuthResponse,
)
from .youtube import (
    find_comment, query_or_fetch_youtube_channel, ChannelInfo, fetch_user_channel,
)
from .db_youtube import YoutubeDbLib
from .settings import settings
from .types import OAuthError, AccountAlreadyLinked, Satoshi
from .db import db
from .core import app


router = APIRouter(prefix='/youtube')
legacy_router = APIRouter()  # For backward compatibility
logger = logging.getLogger(__name__)


class YoutubeVideoResponse(BaseModel):
    id: UUID | None
    total_donated: int


@legacy_router.get('/youtube-video/{video_id}', response_model=YoutubeVideoResponse)
@router.get('/video/{video_id}', response_model=YoutubeVideoResponse)
async def youtube_video_info(video_id: str, db=Depends(get_db_session)):
    try:
        video: YoutubeVideo = await YoutubeDbLib(db).query_youtube_video(video_id=video_id)
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
        youtube_channel: YoutubeChannel = await query_or_fetch_youtube_channel(channel_id=channel_id, db=db)
        is_new = await db.link_youtube_channel(youtube_channel, donator, via_oauth=False)
        if is_new:
            channels.append(youtube_channel)
    return channels


@router.get('/oauth', response_model=OAuthResponse)
async def login_via_google(request: Request, return_to: str, donator=Depends(get_donator)):
    # FIXME: merge to /twitter/oauth
    aiogoogle = Aiogoogle()
    url = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=make_absolute_uri(app.url_path_for('oauth_redirect', provider='youtube')),
            **settings.youtube.oauth.dict(),
        ),
        state=OAuthState(
            error_path=request.headers['referer'],
            success_path=make_absolute_uri(return_to),
            donator_id=donator.id,
        ).to_jwt(),
        prompt='select_account',
        include_granted_scopes=True,
    )
    return OAuthResponse(url=url)


async def finish_youtube_oauth(code: str, donator: Donator) -> Satoshi:
    """
    Returns transferred amount on success linking and raises AccountAlreadyLinked if
    account is already linked
    """
    try:
        channel_info: ChannelInfo = await fetch_user_channel(code)
    except Exception as exc:
        raise OAuthError("Failed to fetch user's channel") from exc
    try:
        async with db.session() as db_session:
            youtube_db = YoutubeDbLib(db_session)
            channel: YoutubeChannel = await query_or_fetch_youtube_channel(channel_id=channel_info.id, db=youtube_db)
            owned_channel: YoutubeChannelOwned = await youtube_db.query_account(id=channel.id)
            if not owned_channel.via_oauth:
                await youtube_db.link_account(channel, donator, via_oauth=True)
                return await youtube_db.transfer_donations(channel, donator)
    except Exception as exc:
        raise OAuthError("Failed to link account") from exc
    else:
        raise AccountAlreadyLinked(owned_channel.owner_id)
