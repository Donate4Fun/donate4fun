import datetime
from uuid import UUID
from xml.etree import ElementTree as ET

from mako.lookup import TemplateLookup
from aiogoogle import Aiogoogle
from fastapi import Request, Form, Query, APIRouter, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from .core import payreq_to_datauri, get_db_session, get_lnd
from .models import DonationRequest, Donation
from .types import Url, UnsupportedTarget
from .youtube import fetch_user_channel, ChannelInfo, validate_target
from .settings import settings
from .lnd import LndClient, Invoice

templates = TemplateLookup(
    directories=['donate4fun/templates'],
    strict_undefined=True,
    imports=['from donate4fun.mako import query'],
)


def TemplateResponse(name, *args, **kwargs) -> HTMLResponse:
    return HTMLResponse(templates.get_template(name).render(*args, **kwargs))


router = APIRouter()


@router.get("/")
async def donate(request: Request, donatee: str | None = Query(...)):
    return TemplateResponse("donate.html", request=request, donatee=donatee)


@router.post("/donate")
async def donate_form(
    request: Request,
    amount: float = Form(...),
    target: Url = Form(...),
    donator: Url = Form(...),
    trigger: Url = Form(...),
    message: Url = Form(...),
    lnd: LndClient = Depends(get_lnd),
):
    try:
        donatee, trigger = await validate_target(target)
    except UnsupportedTarget:
        return TemplateResponse("unsupported.html",  request=request, donatee=donatee)

    invoice: lnd.Invoice = await lnd.create_invoice(memo=f"donate4.fun to {donatee}", amount=amount)
    req = DonationRequest(
        r_hash=invoice.r_hash,
        donator=donator,
        donatee=donatee,
        trigger=trigger,
        message=message,
    )
    return RedirectResponse(request.url_for('donate_invoice', token=req.to_jwt()))


@router.get("/donation/{donation_id}", response_class=HTMLResponse)
async def donate_invoice(request: Request, donation_id: str, db=Depends(get_db_session), lnd=Depends(get_lnd)):
    donation: Donation = await db.query_donation(donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.fetch_invoice(donation.r_hash)
        if invoice.amt_paid > 0:
            await db.donation_paid(donation_id=donation_id, amount=invoice.amt_paid)
        else:
            return TemplateResponse(
                "donation-todo.html",
                request=request,
                qrcode=payreq_to_datauri(invoice.payment_request),
                invoice=invoice,
            )
    return RedirectResponse(request.url_for('donation', id=donation.id))


@router.get('/donation/{donation_id}')
async def donation(request: Request, donation_id: UUID, db=Depends(get_db_session)):
    donation: Donation = await db.query_donation(donation_id=donation_id)
    return TemplateResponse("donation-done.html", request=request, donation=donation)


@router.get('/login/google')
async def login_via_google(request: Request, orig_channel_id: str):
    aiogoogle = Aiogoogle()
    uri = aiogoogle.oauth2.authorization_url(
        client_creds=dict(
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=request.url_for('auth_google'),
            **settings.youtube.oauth.dict(),
        ),
    )
    return RedirectResponse(uri)


@router.get('/auth/google', response_class=JSONResponse)
async def auth_google(
    request: Request, error: str = None, error_description: str = None, code: str = None, db_session=Depends(get_db_session)
):
    if error:
        return {
            'error': error,
            'error_description': error_description
        }
    elif code:
        channel_info: ChannelInfo = await fetch_user_channel(request, code)
        donations = await db_session.query_donations(donatee=channel_info.url)
        return dict(channel=channel_info.id, donations=donations)
    else:
        # Should either receive a code or an error
        raise Exception("Something's probably wrong with your callback")


@router.get('/donatee')
async def donatee(request: Request, donatee: Url = Query(...), db_session=Depends(get_db_session)):
    donations = await db_session.query_donations(donatee=donatee)
    sum_unclaimed = sum(d.amount for d in donations if d.claimed_at is None) / 1000
    return TemplateResponse(
        "donatee.html",
        request=request,
        sum_donated=sum(d.amount for d in donations) / 1000,
        sum_unclaimed=sum_unclaimed,
        is_claim_allowed=sum_unclaimed >= settings.min_withdrawal,
        donatee=donatee,
        donations=donations,
    )


@router.post('/claim')
async def claim(request: Request, donatee: Url = Query(...), db_session=Depends(get_db_session)):
    donations = await db_session.query_donations(donatee=donatee)
    for donation in donations:
        pass


@router.get('/donator/{donator}')
async def donator(request: Request, donator: str):
    return None


@router.get('/donations')
async def donations(request: Request, db_session=Depends(get_db_session)):
    donations = await db_session.query_donations(donatee=donatee)
    return TemplateResponse("donations.html", request, donations=donations)


@router.get('/sitemap.xml')
@router.get('/sitemap3.xml')
@router.get('/sitemap4.xml')
async def sitemap(request: Request, db_session=Depends(get_db_session)):
    base_url = settings.youtube.oauth.redirect_base_url
    urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for youtube_channel in await db_session.query_youtube_channels():
        url = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url, 'loc')
        loc.text = f'{base_url}/youtube-channel/{youtube_channel.id}'
        lastmod = ET.SubElement(url, 'lastmod')
        lastmod.text = datetime.date.today().isoformat()
        changefreq = ET.SubElement(url, 'changefreq')
        changefreq.text = 'weekly'
    return Response(content=ET.tostring(urlset, xml_declaration=True, encoding='UTF-8'), media_type="application/xml")
