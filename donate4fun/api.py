from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from .core import validate_target, query_lnd
from .youtube import YoutubeDonatee

router = APIRouter()


class DonateRequest(BaseModel):
    target: HttpUrl
    amount: int
    message: str | None
    donater: str | None


class DonateResponse(BaseModel):
    r_hash: str
    payment_request: str
    donatee: HttpUrl
    trigger: HttpUrl


@router.post("/donate", response_model=DonateResponse)
async def donate(request: DonateRequest):
    donatee: YoutubeDonatee = await validate_target(request.target)

    invoice = await query_lnd('POST', '/v1/invoices', memo=f"donate4.fun to {donatee.name}", value=request.amount)
    return DonateResponse(
        r_hash=invoice['r_hash'],
        payment_request=invoice["payment_request"],
        donatee=donatee.url,
        trigger=donatee.trigger,
        name=donatee.name,
    )
