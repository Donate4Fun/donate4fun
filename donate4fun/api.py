import logging
from uuid import UUID, uuid4
from typing import Callable

from fastapi import APIRouter, WebSocket, Request, Response, Depends
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError
from httpx import HTTPStatusError

from .core import validate_target, get_db_session, get_lnd
from .models import Donation, Donator, Invoice, DonateResponse, DonateRequest, DonationPaidResponse
from .types import ValidationError, RequestHash
from .youtube import YoutubeDonatee
from .db import Database

logger = logging.getLogger(__name__)


class CustomRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except HTTPStatusError as exc:
                logger.debug(f"{request.url}: Upstream error", exc_info=exc)
                status_code = exc.response.status_code
                body = exc.response.json()
                return JSONResponse(status_code=500, content={"message": f"Upstream server returned {status_code}: {body}"})
            except (ValidationError, PydanticValidationError) as exc:
                logger.debug(f"{request.url}: Validation error", exc_info=exc)
                return JSONResponse(
                    status_code=400,
                    content={"message": repr(exc)},
                )

        return custom_route_handler


router = APIRouter(route_class=CustomRoute)


def get_donator(request: Request):
    if donator_id := request.session.get('donator'):
        donator = Donator(id=UUID(donator_id))
    else:
        donator = Donator(id=uuid4())
        request.session['donator'] = str(donator.id)
    return donator


@router.post("/donate", response_model=DonateResponse)
async def donate(
    request: DonateRequest, donator: Donator = Depends(get_donator), db_session=Depends(get_db_session), lnd=Depends(get_lnd),
 ) -> DonateResponse:
    logger.debug(f"Donator {donator.id} wants to donate {request.amount} to {request.target}")
    donatee: YoutubeDonatee = await validate_target(request.target)
    invoice: Invoice = await lnd.create_invoice(memo=f"Donate4.fun to {donatee.channel.title}", value=request.amount)
    youtube_channel_id: UUID = await db_session.get_or_create_youtube_channel(
        channel_id=donatee.channel.id, title=donatee.channel.title, thumbnail_url=donatee.channel.thumbnail,
    )
    donation: Donation = await db_session.create_donation(
        r_hash=invoice.r_hash, amount=invoice.value, youtube_channel_id=youtube_channel_id, donator_id=donator.id,
    )
    return DonateResponse(donation=donation, payment_request=invoice.payment_request)


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def donation(donation_id: UUID, db_session=Depends(get_db_session), lnd=Depends(get_lnd)):
    donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.lookup_invoice(donation.r_hash)
        if invoice.state == 'CANCELED':
            logger.debug(f"Invoice {invoice} cancelled, recreating")
            invoice = await lnd.create_invoice(memo=invoice.memo, value=invoice.value)
            await db_session.update_donation(donation_id=donation_id, r_hash=invoice.r_hash)
        payment_request = invoice.payment_request
    else:
        payment_request = None
    return DonateResponse(donation=donation, payment_request=payment_request)


@router.websocket("/donation/subscribe/{donation_id}")
async def subscribe_to_donation(websocket: WebSocket, donation_id: UUID):
    logger.debug("Connected /donation/subscribe/")
    db: Database = websocket.app.db
    try:
        async with db.pubsub() as sub:
            async for msg in sub.listen_for_donations():
                if msg is None:
                    await websocket.accept()
                    logger.debug(f"Accepted ws connection for {donation_id}")
                elif msg == donation_id:
                    async with db.session() as db_session:
                        donation: Donation = await db_session.query_donation(id=donation_id)
                    if donation.paid_at is not None:
                        await websocket.send_text(DonationPaidResponse(status="ok", donation=donation).json())
                    else:
                        logger.warning(f"Received notification about already paid donation {donation_id}")
                    break
                else:
                    logger.debug(f"Received notification about donation {donation.id}, skipping")
    except Exception as exc:
        logger.exception("Exception while listening for donations")
        await websocket.send_json(dict(status='error', error=repr(exc)))
    finally:
        await websocket.close()


@router.post("/donation/cancel/{donation_id}")
async def cancel_donation(donation_id: UUID, db=Depends(get_db_session), lnd=Depends(get_lnd)):
    """
    It only works for HODL invoices
    """
    r_hash: RequestHash = await db.cancel_donation(donation_id)
    await lnd.cancel_invoice(r_hash)


@router.get("/latest-donations", response_model=list[Donation])
async def donations(db=Depends(get_db_session)):
    return await db.query_recent_donations()


class StatusResponse(BaseModel):
    db: str
    lnd: str


@router.get("/status")
async def status(db=Depends(get_db_session), lnd=Depends(get_lnd)):
    return StatusResponse(
        db=await db.query_status(),
        lnd=await lnd.query_state(),
    )
