import json
import datetime
from uuid import UUID
from typing import Any
from xml.etree import ElementTree as ET

import httpx
from mako.lookup import TemplateLookup
from aiogoogle import Aiogoogle
from fastapi import Request, Response, FastAPI, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from .api_utils import get_db_session
from .models import YoutubeChannel
from .youtube import fetch_user_channel, ChannelInfo, query_or_fetch_youtube_channel
from .settings import settings


app = FastAPI()


async def fetch_manifest() -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f'http://localhost:{settings.frontend_port}/manifest.json')
        return resp.json()


@app.get("/")
@app.get("/youtube/{youtube_channel_id}")
@app.get("/twitter/{twitter_account_id}")
async def index(request: Request, youtube_channel_id: UUID | None = None, twitter_account_id: UUID | None = None):
    if twitter_account_id is not None:
        og_image_path = f'/preview/twitter/{twitter_account_id}'
    elif youtube_channel_id is not None:
        og_image_path = f'/preview/youtube/{youtube_channel_id}'
    else:
        og_image_path = '/static/sharing.png'
    manifest = await fetch_manifest() if settings.release else None
    return TemplateResponse(
        "index.html", request=request, og_image_path=og_image_path, manifest=manifest,
    )


@app.get('/login/google')
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


@app.get('/auth/google', response_class=JSONResponse)
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


@app.get('/.well-known/lnurlp/{username}')
async def lightning_address(request: Request, username: str):
    return dict(
        callback=request.app.url_path_for('payment_callback').make_absolute_url(settings.lnd.lnurl_base_url),
        maxSendable=1000000,
        minSendable=100,
        metadata=json.dumps([
            ("text/identifier", f'{username}@{request.host}'),
            ("text/plain", f"Sats for {username}"),
        ]),
        commentAllowed=255,
        tag="payRequest",
    )


templates = TemplateLookup(
    directories=['donate4fun/templates'],
    strict_undefined=True,
    imports=['from donate4fun.mako import query'],
)


def TemplateResponse(name, *args, **kwargs) -> HTMLResponse:
    return HTMLResponse(templates.get_template(name).render(*args, settings=settings, **kwargs))
