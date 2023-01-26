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

from playwright.async_api import async_playwright, ConsoleMessage, Error as PlaywrightError
from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.responses import Response
from async_lru import alru_cache

from .core import register_command
from .settings import settings
from .models import TwitterAccount, Donation
from .db import db
from .db_twitter import TwitterDbLib
from .db_donations import DonationsDbLib
from .web import TemplateResponse

logger = logging.getLogger(__name__)


class ScreenshotError(Exception):
    pass


def chromium_flags():
    return ['--disable-gpu']


class Screenshoter:
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.lock = asyncio.Lock()

    async def get_browser(self):
        if self.browser is None or not self.browser.is_connected():
            if self.browser:
                await self.browser.close()
            self.browser = await self.playwright.chromium.launch(args=chromium_flags())
            logger.info("Started Chromium")
        return self.browser

    async def take_screenshot(self, path: str, **params) -> bytes:
        async with self.lock:
            return await self.take_screenshot_impl(path, **params)

    @alru_cache(maxsize=3)  # Twitter bot likes to make a lot of parallel requests for the same image if we respnod a bit slow
    async def take_screenshot_impl(self, path: str, **params) -> bytes:
        start = time.time()
        browser = await self.get_browser()
        page = await browser.new_page(device_scale_factor=2)
        try:
            page.on("request", lambda request: logger.trace("request %s %s", request.method, request.url))
            page.on("response", lambda response: logger.trace("response %s %s", response.status, response.url))
            error_messages = []

            def console_msg(msg: ConsoleMessage):
                logger.trace("console: %r", msg)
                if msg.type == 'error':
                    error_messages.append(msg)
            page.on("console", console_msg)
            await page.goto(f'http://localhost:{settings.api_port}/preview/{path}?{urlencode(params)}')
            await page.evaluate('() => document.fonts.ready')
            result = await page.locator('body').screenshot()
            if error_messages:
                raise ScreenshotError(f"Browser console has error messages: {error_messages}")
            return result
        except PlaywrightError:
            logger.exception("Error in PlayWright")
            await browser.close()
            raise
        finally:
            await page.close()
            logger.trace("Screenshot of %s took %fs", path, time.time() - start)


async def get_screenshoter(request: Request):
    return request.app.screenshoter


@asynccontextmanager
async def run_screenshoter():
    async with async_playwright() as pw:
        logger.info("Started Chromium screenshoter")
        yield Screenshoter(pw)


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
        account: TwitterAccount = await TwitterDbLib(db_session).query_account(id=account_id)
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
        donation: Donation = await DonationsDbLib(db_session).query_donation(id=donation_id)
    if donation.twitter_account:
        png_image: bytes = await screenshoter.take_screenshot(
            'twitter-donation-sharing.html',
            json=TwitterDonationShareInfo(
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
