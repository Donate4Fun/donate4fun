from uuid import UUID, uuid4
from typing import Callable

from fastapi import APIRouter, WebSocket, Request, Response, Depends
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, ValidationError as PydanticValidationError

from .core import validate_target, base64_to_hex, get_db_session
from .models import Donation, Donator
from .types import ValidationError, RequestHash
from .youtube import YoutubeDonatee, ChannelInfo
from .db import DbSession
from . import lnd


class CustomRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except (ValidationError, PydanticValidationError) as exc:
                return JSONResponse(
                    status_code=400,
                    content={"message": repr(exc)},
                )

        return custom_route_handler


router = APIRouter(route_class=CustomRoute)


class DonateRequest(BaseModel):
    target: HttpUrl
    amount: int
    message: str | None
    donater: str | None


class DonateResponse(BaseModel):
    r_hash: str
    payment_request: str
    channel: ChannelInfo
    trigger: HttpUrl | None


def get_donator(request: Request):
    if donator_id := request.session.get('donator'):
        donator = Donator(id=UUID(donator_id))
    else:
        donator = Donator(id=uuid4())
        request.session['donator'] = str(donator.id)
    return donator


@router.post("/donate", response_model=DonateResponse)
async def donate(request: DonateRequest, donator: Donator = Depends(get_donator), db: DbSession = Depends(get_db_session)):
    donatee: YoutubeDonatee = await validate_target(request.target)
    invoice: lnd.Invoice = await lnd.create_invoice(memo=f"Donate4.fun to {donatee.channel.title}", amount=request.amount)
    youtube_channel_id: UUID = await db.get_or_create_youtube_channel(
        channel_id=donatee.channel.id, title=donatee.channel.title, thumbnail_url=donatee.channel.thumbnail,
    )
    await db.create_donation(
        r_hash=invoice.r_hash, amount=invoice.amount, youtube_channel_id=youtube_channel_id, donator_id=donator.id,
    )
    return DonateResponse(
        r_hash=base64_to_hex(invoice.r_hash),
        payment_request=invoice.payment_request,
        channel=donatee.channel,
        trigger=donatee.trigger,
    )


@router.websocket("/donation/subscribe/{donation_id}")
async def subscribe_to_donation(websocket: WebSocket, donation_id: UUID, db=Depends(get_db_session)):
    await websocket.accept()
    try:
        async for msg in db.listen_for_donations():
            if msg not in (None, donation_id):
                continue
            donation: Donation = await db.query_donation(donation_id)
            if donation.paid_at is not None:
                await websocket.send_json(dict(status="ok", donation=donation.dict()))
                break
    except Exception as exc:
        await websocket.send_json(dict(status='error', error=repr(exc)))


@router.post("/invoice/cancel/{donation_id}")
async def cancel_invoice(donation_id: UUID, db: DbSession = Depends(get_db_session)):
    r_hash: RequestHash = await db.cancel_invoice(donation_id)
    await lnd.cancel_invoice(r_hash)


@router.get("/latest-donations", response_model=list[Donation])
async def donations(db=Depends(get_db_session)):
    return await db.query_recent_donations()
