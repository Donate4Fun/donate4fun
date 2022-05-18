from base64 import b64decode, b64encode
import io
import binascii
import os.path
import re
from uuid import UUID
from urllib.parse import urlparse
from typing import Any

import httpx
import qrcode
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
#from fastapi.templating import Jinja2Templates
from mako.lookup import TemplateLookup
from qrcode.image.pure import PymagingImage
from aiogoogle import Aiogoogle
from hypercorn.asyncio import serve
from hypercorn.config import Config
from email_validator import validate_email
from debug_toolbar.middleware import DebugToolbarMiddleware
from .settings import settings, load_settings
from .db import db, init_db
from .youtube import validate_youtube_url, get_user_channel, make_youtube_channel_url
from .models import DonationRequest, Donation, UnsupportedDonatee

Url = str
PaymentRequest = str
#templates = Jinja2Templates(directory="donate4fun/templates")
templates = TemplateLookup(
    directories=['donate4fun/templates'],
    strict_undefined=True,
    imports=['from donate4fun.mako import query'],
)
#TemplateResponse = templates.TemplateResponse


def TemplateResponse(name, *args, **kwargs) -> HTMLResponse:
    return HTMLResponse(templates.get_template(name).render(*args, **kwargs))


app = FastAPI(debug=True)
app.add_middleware(DebugToolbarMiddleware)
app.mount("/static", StaticFiles(directory="donate4fun/static"), name="static")


async def main():
    with load_settings():
        async with init_db():
            config = Config.from_mapping(settings().hypercorn)
            await serve(app, config)


@app.get("/")
async def donate(request: Request, donatee: str | None = Query(...)):
    return TemplateResponse("donate.html", request=request, donatee=donatee)


async def validate_donatee(donatee: str):
    if re.match(r'https?://.+', donatee):
        return await validate_donatee_url(donatee)
    return validate_email(donatee).email


async def validate_donatee_url(donatee: Url):
    parsed = urlparse(donatee)
    if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be']:
        return await validate_youtube_url(parsed)
    else:
        raise UnsupportedDonatee


def datauri(pay_req: PaymentRequest):
    """
    converts ln payment request to qr code in form of data: uri
    """
    img = qrcode.make(pay_req, image_factory=PymagingImage)
    data = io.BytesIO()
    img.save(data)
    encoded = b64encode(data.getvalue()).decode()
    return 'data:image/png;base64,' + encoded


def load_invoice_macaroon() -> str:
    return binascii.hexlify(open(os.path.expanduser("~/.lnd/data/chain/bitcoin/mainnet/invoices.macaroon"), "rb").read())


async def query_lnd(method: str, api: str, **request: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=method,
            url=f'{settings.get().lnd_url}{api}',
            json=request,
            headers={"Grpc-Metadata-macaroon": load_invoice_macaroon()},
        )
        return resp.json()


@app.post("/donate")
async def donate_form(
    request: Request,
    amount: float = Form(...),
    donatee: Url = Form(...),
    donator: Url = Form(...),
    trigger: Url = Form(...),
    message: Url = Form(...),
):
    try:
        donatee: Url = await validate_donatee(donatee)
    except UnsupportedDonatee:
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
        async with Aiogoogle() as aiogoogle:
            full_user_creds = await aiogoogle.oauth2.build_user_creds(
                grant=code,
                client_creds=dict(
                    redirect_uri=request.url_for('auth_google'),
                    **settings.get().youtube.oauth.dict(),
                ),
            )
        channel_id = await get_user_channel(full_user_creds)
        donations = await db().query_donations(donatee=make_youtube_channel_url(channel_id))
        return dict(channel=channel_id, donations=donations)
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


@app.get('/donator/{donator}')
async def donator(request: Request, donator: str):
    return None
