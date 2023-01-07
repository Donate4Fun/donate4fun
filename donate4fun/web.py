import datetime
from uuid import UUID
from typing import Any
from xml.etree import ElementTree as ET

import httpx
from mako.lookup import TemplateLookup
from fastapi import Request, Response, FastAPI, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm.exc import NoResultFound

from .api_utils import get_db_session
from .models import YoutubeChannel, TwitterAccount, Donation, Donator
from .youtube import query_or_fetch_youtube_channel
from .twitter import query_or_fetch_twitter_account
from .settings import settings
from .db import db
from .db_models import DonatorDb
from .lnd import lightning_payment_metadata

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return await exception_handler(request, exc, 422)


@app.exception_handler(NoResultFound)
async def not_found_exception_handler(request, exc):
    return await exception_handler(request, exc, 404)


async def exception_handler(request, exc, status_code):
    if request.headers['accept'].startswith('application/json'):
        return JSONResponse(dict(
            status="ERROR",
            exception_type=type(exc).__name__,
            message=str(exc),
        ), status_code=status_code)
    else:
        manifest = await fetch_manifest() if settings.release else None
        return TemplateResponse('error.html', request=request, exception=exc, manifest=manifest, status_code=status_code)


async def fetch_manifest() -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f'http://localhost:{settings.frontend_port}/manifest.json')
        return resp.json()


def target_name(donation: Donation) -> str:
    if receiver := donation.receiver:
        return receiver.name
    elif channel := donation.youtube_channel:
        return channel.title
    elif account := donation.twitter_account:
        return account.name
    else:
        raise ValueError("donation has no target")


def default_sharing_image():
    return '/static/sharing.png?v=2'


@app.get("/youtube/{object_id}")
@app.get("/twitter/{object_id}")
@app.get("/donation/{object_id}")
async def index(request: Request, object_id: UUID | None = None, full_path: str | None = None):
    if object_id is not None:
        object_type = request.url.path.split('/')[1]
        og_image_path = f'/preview/{object_type}/{object_id}'
    else:
        object_type = None
        og_image_path = default_sharing_image()
    manifest = await fetch_manifest() if settings.release else None
    if object_type == 'donation':
        async with db.session() as db_session:
            donation: Donation = await db_session.query_donation(id=object_id)
        description = f"{donation.amount} sats was donated to {target_name(donation)}"
    else:
        description = "Support creators with Bitcoin Lightning donations"
    return TemplateResponse(
        "index.html", request=request, og_image_path=og_image_path, manifest=manifest, description=description,
    )


@app.get('/sitemap.xml')
async def sitemap(request: Request, db_session=Depends(get_db_session)):
    base_url = settings.base_url
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


@app.get('/d/{channel_id}')
async def donate_redirect(request: Request, channel_id: str, db=Depends(get_db_session)):
    youtube_channel: YoutubeChannel = await query_or_fetch_youtube_channel(channel_id=channel_id, db=db)
    return RedirectResponse(f'{settings.base_url}/donate/{youtube_channel.id}', status_code=302)


@app.get('/tw/{handle}')
async def twitter_account_redirect(request: Request, handle: str, db=Depends(get_db_session)):
    account: TwitterAccount = await query_or_fetch_twitter_account(handle=handle, db=db)
    return RedirectResponse(f'{settings.base_url}/twitter/{account.id}', status_code=302)


@app.get('/.well-known/lnurlp/{username}', response_class=JSONResponse)
async def lightning_address(request: Request, username: str, db_session=Depends(get_db_session)):
    receiver: Donator = await db_session.find_donator(DonatorDb.lightning_address == f'{username}@{request.headers["host"]}')
    return dict(
        status='OK',
        callback=f'{settings.base_url}/api/v1/lnurl/{receiver.id}/payment-callback',
        maxSendable=settings.lnurlp.max_sendable_sats * 1000,
        minSendable=settings.lnurlp.min_sendable_sats * 1000,
        metadata=lightning_payment_metadata(receiver),
        commentAllowed=255,
        tag="payRequest",
    )


templates = TemplateLookup(
    directories=['donate4fun/templates'],
    strict_undefined=True,
    imports=['from donate4fun.mako import query'],
)


def TemplateResponse(name, *args, status_code=200, **kwargs) -> HTMLResponse:
    return HTMLResponse(templates.get_template(name).render(*args, settings=settings, **kwargs), status_code=status_code)


# This route should be last declared
@app.get("/{full_path:path}")
async def default_index(request: Request, full_path: str):
    og_image_path = default_sharing_image()
    manifest = await fetch_manifest() if settings.release else None
    description = "Support creators with Bitcoin Lightning donations"
    return TemplateResponse(
        "index.html", request=request, og_image_path=og_image_path, manifest=manifest, description=description,
    )
