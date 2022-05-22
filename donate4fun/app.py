import binascii
from base64 import b64decode
from uuid import UUID

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from mako.lookup import TemplateLookup
from aiogoogle import Aiogoogle
from hypercorn.asyncio import serve
from hypercorn.config import Config
from debug_toolbar.middleware import DebugToolbarMiddleware
from .settings import settings, load_settings
from .db import db, init_db
from .models import DonationRequest, Donation, UnsupportedTarget, ValidationError
from .core import Url, query_lnd, datauri, validate_target
from .youtube import fetch_user_channel, ChannelInfo
from . import api

templates = TemplateLookup(
    directories=['donate4fun/templates'],
    strict_undefined=True,
    imports=['from donate4fun.mako import query'],
)


def TemplateResponse(name, *args, **kwargs) -> HTMLResponse:
    return HTMLResponse(templates.get_template(name).render(*args, **kwargs))


app = FastAPI(debug=True)
app.add_middleware(DebugToolbarMiddleware)
app.mount("/static", StaticFiles(directory="donate4fun/static"), name="static")
app.include_router(api.router, prefix="/api/v1")


@app.exception_handler(ValidationError)
async def not_found_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"message": repr(exc)},
    )


async def main():
    with load_settings():
        async with init_db():
            config = Config.from_mapping(settings().hypercorn)
            await serve(app, config)


@app.get("/")
async def donate(request: Request, donatee: str | None = Query(...)):
    return TemplateResponse("donate.html", request=request, donatee=donatee)


@app.post("/donate")
async def donate_form(
    request: Request,
    amount: float = Form(...),
    target: Url = Form(...),
    donator: Url = Form(...),
    trigger: Url = Form(...),
    message: Url = Form(...),
):
    try:
        donatee, trigger = await validate_target(target)
    except UnsupportedTarget:
        return TemplateResponse("unsupported.html",  request=request, donatee=donatee)

    invoice = await query_lnd('POST', '/v1/invoices', memo=f"donate4.fun to {donatee}", value_msat=int(amount * 1000))
    r_hash = invoice["r_hash"]
    req = DonationRequest(
        r_hash=r_hash,
        donator=donator,
        donatee=donatee,
        trigger=trigger,
        message=message,
    )
    return RedirectResponse(request.url_for('donate_invoice', token=req.to_jwt()))


@app.get("/donate/{token}", response_class=HTMLResponse)
async def donate_invoice(request: Request, token: str):
    req: DonationRequest = DonationRequest.from_jwt(token)
    donation: Donation = await db().query_donation(req.r_hash)
    if donation is None:
        r_hash = binascii.b2a_hex(b64decode(req.r_hash)).decode()
        invoice = await query_lnd('GET', f'/v1/invoice/{r_hash}')
        pay_req = invoice["payment_request"]
        amount = invoice["value_msat"]
        amount_paid = int(invoice["amt_paid_msat"])
        if amount_paid > 0:
            donation = await db().create_donation(amount_paid, req)
        else:
            return TemplateResponse(
                "donation-todo.html", request=request, qrcode=datauri(pay_req), pay_req=pay_req, amount=amount, req=req,
            )
    return RedirectResponse(request.url_for('donation', id=donation.id))


@app.get('/donation/{id}')
async def donation(request: Request, id: UUID):
    donation: Donation = await db().query_donation(id=id)
    return TemplateResponse("donation-done.html", request=request, donation=donation)


@app.get('/login/google')
async def login_via_google(request: Request, orig_channel_id: str):
    aiogoogle = Aiogoogle()
    uri = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=request.url_for('auth_google'),
            **settings.get().youtube.oauth.dict(),
        ),
    )
    return RedirectResponse(uri)


@app.get('/auth/google', response_class=JSONResponse)
async def auth_google(request: Request, error: str = None, error_description: str = None, code: str = None):
    if error:
        return {
            'error': error,
            'error_description': error_description
        }
    elif code:
        channel_info: ChannelInfo = await fetch_user_channel(request, code)
        donations = await db().query_donations(donatee=channel_info.url)
        return dict(channel=channel_info.id, donations=donations)
    else:
        # Should either receive a code or an error
        raise Exception("Something's probably wrong with your callback")


@app.get('/donatee')
async def donatee(request: Request, donatee: Url = Query(...)):
    donations = await db().query_donations(donatee=donatee)
    sum_unclaimed = sum(d.amount for d in donations if d.claimed_at is None) / 1000
    return TemplateResponse(
        "donatee.html",
        request=request,
        sum_donated=sum(d.amount for d in donations) / 1000,
        sum_unclaimed=sum_unclaimed,
        is_claim_allowed=sum_unclaimed >= settings().claim_limit,
        donatee=donatee,
        donations=donations,
    )


@app.post('/claim')
async def claim(request: Request, donatee: Url = Query(...)):
    donations = await db().query_donations(donatee=donatee)
    for donation in donations:
        pass


@app.get('/donator/{donator}')
async def donator(request: Request, donator: str):
    return None


@app.get('/donations')
async def donations(request: Request):
    donations = await db().query_donations(donatee=donatee)
    return TemplateResponse("donations.html", request, donations=donations)
