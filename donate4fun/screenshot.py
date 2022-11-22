import webbrowser
import tempfile
import asyncio
import logging
import time
from json import loads
from uuid import UUID
from types import SimpleNamespace
from contextlib import asynccontextmanager
from urllib.parse import urlencode, parse_qs

from playwright.async_api import async_playwright, ConsoleMessage
from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.responses import Response

from .core import register_command
from .settings import settings
from .models import TwitterAccount, Donation
from .db import db
from .web import TemplateResponse

logger = logging.getLogger(__name__)


class ScreenshotError(Exception):
    pass


class Screenshoter:
    def __init__(self, browser):
        self.browser = browser

    async def take_screenshot(self, path: str, **params) -> bytes:
        start = time.time()
        page = await self.browser.new_page(device_scale_factor=2)
        try:
            api_port: str = settings.hypercorn['bind'].split(':')[-1]
            page.on("request", lambda request: logger.trace("request %s %s", request.method, request.url))
            page.on("response", lambda response: logger.trace("response %s %s", response.status, response.url))
            error_messages = []

            def console_msg(msg: ConsoleMessage):
                logger.trace("console: %r", msg)
                if msg.type == 'error':
                    error_messages.append(msg)
            page.on("console", console_msg)
            await page.goto(f'http://localhost:{api_port}/preview/{path}?{urlencode(params)}')
            result = await page.locator('body').screenshot()
            if error_messages:
                raise ScreenshotError(f"Browser console has error messages: {error_messages}")
            return result
        finally:
            await page.close()
            logger.trace("Screenshot of %s took %fs", path, time.time() - start)


async def get_screenshoter(request: Request):
    return request.app.screenshoter


@asynccontextmanager
async def run_screenshoter():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        logger.info("Started Chromium screenshoter")
        try:
            yield Screenshoter(browser)
        finally:
            await browser.close()


@register_command
async def take_screenshot(path: str, params: str):
    async with run_screenshoter() as screenshoter:
        png_image: bytes = await screenshoter.take_screenshot(path, **{k: v[0] for k, v in parse_qs(params).items()})
        with tempfile.NamedTemporaryFile() as file:
            file.write(png_image)
            webbrowser.open(file.name)
            await asyncio.sleep(5)


router = APIRouter()


def get_static_url(filename):
    return f'//localhost:{settings.frontend_port}/static/{filename}'


def parse(data):
    if type(data) is list:
        return list(map(parse, data))
    elif type(data) is dict:
        sns = SimpleNamespace()
        for key, value in data.items():
            setattr(sns, key, parse(value))
        return sns
    else:
        return data


@router.get("/{path}")
async def sharing_image(request: Request, path: str, json: str | None = None):
    if json:
        query = parse(loads(json))
    else:
        query = SimpleNamespace(**request.query_params)
    return TemplateResponse(path, request=request, static=get_static_url, q=query)


@router.get("/twitter/{account_id}")
async def twitter_image(account_id: UUID, screenshoter=Depends(get_screenshoter)):
    async with db.session() as db_session:
        account: TwitterAccount = await db_session.query_twitter_account(id=account_id)
    png_image: bytes = await screenshoter.take_screenshot(
        'twitter-account-sharing.html',
        handle=account.handle,
        profile_image=account.profile_image_url.replace('_normal', '_x96'),
    )
    return Response(content=png_image, media_type='image/png')


class TwitterDonationShareInfo(Donation):
    donator_twitter_account: TwitterAccount | None


@router.get("/donation/{donation_id}")
async def donation_image(donation_id: UUID, screenshoter=Depends(get_screenshoter)):
    async with db.session() as db_session:
        donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.twitter_account:
        png_image: bytes = await screenshoter.take_screenshot(
            'twitter-donation-sharing.html',
            json=TwitterDonationShareInfo(
                donator_twitter_account=None,
                **donation.dict(),
            ).json(),
        )
    elif donation.youtube_channel:
        raise ValueError("not implemented for YouTube")
    return Response(content=png_image, media_type='image/png')


@asynccontextmanager
async def create_screenshoter_app():
    app = FastAPI()
    app.include_router(router)
    async with run_screenshoter() as screenshoter:
        app.screenshoter = screenshoter
        yield app
