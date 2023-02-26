import datetime
from uuid import UUID
from typing import Any
from xml.etree import ElementTree as ET

import httpx
from mako.lookup import TemplateLookup
from fastapi import Request, Response, FastAPI, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from furl import furl
from sqlalchemy.orm.exc import NoResultFound
from jwcrypto.jwk import JWK

from .api_utils import get_db_session, make_absolute_uri
from .models import YoutubeChannel, Donation, Donator, SocialProviderId, SocialProviderSlug, SocialAccount
from .social import SocialProvider
from .youtube_provider import YoutubeProvider
from .settings import settings
from .db import db
from .db_models import DonatorDb
from .db_youtube import YoutubeDbLib
from .db_twitter import TwitterDbLib
from .db_donations import DonationsDbLib
from .lnd import lightning_payment_metadata
from .donation import LnurlpClient, lightning_address_to_lnurlp

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
    elif user := donation.github_user:
        return user.name
    else:
        raise ValueError("donation has no target")


def default_sharing_image():
    return '/static/sharing.png?v=2'


@app.get("/youtube/{object_id}")
@app.get("/twitter/{object_id}")
@app.get("/github/{object_id}")
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
            donation: Donation = await DonationsDbLib(db_session).query_donation(id=object_id)
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

    for youtube_channel in await YoutubeDbLib(db_session).query_accounts():
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
    youtube_channel: YoutubeChannel = await YoutubeProvider().query_or_fetch_account(channel_id=channel_id, db=YoutubeDbLib(db))
    return RedirectResponse(make_absolute_uri(f'/donate/{youtube_channel.id}'), status_code=302)


# These slugs should match SocialProviderSlug values
@app.get('/tw/{handle}')
@app.get('/yt/{handle}')
@app.get('/gh/{handle}')
@app.get('/d4f/{handle}')
async def social_account_redirect(request: Request, handle: str, db=Depends(get_db_session)):
    provider_slug: str = furl(request.url.path).path.segments[0]
    provider: SocialProvider = SocialProvider.from_slug(SocialProviderSlug(provider_slug))
    account: SocialAccount = await provider.query_or_fetch_account(handle=handle, db=TwitterDbLib(db))
    return RedirectResponse(make_absolute_uri(provider.get_account_path(account)), status_code=302)


@app.get('/.well-known/lnurlp/{username}', response_class=JSONResponse)
@app.get('/.well-known/lnurlp/{provider_id}/{username}', response_class=JSONResponse)
async def lightning_address(
    request: Request, username: str, provider_id: SocialProviderId = 'donate4fun', db_session=Depends(get_db_session),
):
    if provider_id == 'donate4fun':
        account: Donator = await db_session.find_donator(DonatorDb.lightning_address == f'{username}@{request.headers["host"]}')
    else:
        provider: SocialProvider = SocialProvider.create(provider_id)
        async with db.session() as db_session:
            account: SocialAccount = await provider.query_or_fetch_account(db=provider.wrap_db(db_session), handle=username)
            if account.lightning_address:
                # Pay directly to a lightning address provider
                async with LnurlpClient() as client:
                    metadata: dict = await client.fetch_metadata(lightning_address_to_lnurlp(account.lightning_address))
                    return metadata
    return dict(
        status='OK',
        callback=make_absolute_uri(f'/api/v1/lnurl/{provider_id}/{account.id}/payment-callback'),
        maxSendable=settings.lnurlp.max_sendable_sats * 1000,
        minSendable=settings.lnurlp.min_sendable_sats * 1000,
        metadata=lightning_payment_metadata(account),
        commentAllowed=255,
        tag="payRequest",
    )


@app.get('/lnurlp/{provider}/{username}')
async def lnurlp_redirect(provider: str, username: str):
    url = furl(make_absolute_uri(f'/.well-known/lnurlp/{provider}/{username}'), scheme='lnurlp').url
    return RedirectResponse(url, status_code=302)


@app.get("/.well-known/openid-configuration", response_class=JSONResponse)
async def openid_configuration():
    return dict(
        issuer=make_absolute_uri(""),
        jwks_uri=make_absolute_uri(".well-known/jwks.json"),
    )


@app.get("/.well-known/jwks.json", response_class=JSONResponse)
async def jwks_json():
    return dict(keys=[JWK(**settings.jwt.jwk).export_public(as_dict=True)])


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
