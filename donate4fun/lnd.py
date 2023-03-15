import binascii
import asyncio
import os.path
import json
import logging
import math
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from functools import cached_property
from typing import Any
from typing import Literal

import asyncpg
import httpx
import sqlalchemy
from lnpayencode import LnAddr
from lnurl.helpers import _lnurl_decode
from lnurl.models import LnurlResponseModel
from lnurl.types import MilliSatoshi
from pydantic import Field, AnyUrl, BaseModel
from pydantic.datetime_parse import parse_datetime

from .settings import LndSettings, settings
from .types import RequestHash, PaymentRequest
from .models import Donator, Donation, SocialAccount
from .core import as_task, ContextualObject, from_base64, to_base64
from .api_utils import donation_paid, register_app_command
from .db_donations import DonationsDbLib

logger = logging.getLogger(__name__)
State = str


class PayInvoiceError(Exception):
    pass


class LndIsNotReady(Exception):
    pass


class NaiveDatetime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        return parse_datetime(int(v)).replace(tzinfo=None)


class Invoice(BaseModel):
    """
    This model is replica of lnd's Invoice message
    https://github.com/lightningnetwork/lnd/blob/master/lnrpc/lightning.proto#L3314
    """
    r_hash: RequestHash
    payment_request: PaymentRequest
    value: int | None
    memo: str | None
    settle_date: NaiveDatetime | None
    amt_paid_sat: int | None
    state: str | None


class PayInvoiceResult(BaseModel):
    creation_date: NaiveDatetime
    fee: float
    fee_msat: int
    fee_sat: float
    payment_hash: RequestHash
    payment_preimage: RequestHash
    status: str
    failure_reason: str
    value: float
    value_msat: int
    value_sat: float


class LnurlWithdrawResponse(LnurlResponseModel):
    """
    Override default lnurl model to allow http:// callback urls
    """
    tag: Literal["withdrawRequest"] = "withdrawRequest"
    callback: AnyUrl
    k1: str
    min_withdrawable: MilliSatoshi = Field(..., alias="minWithdrawable")
    max_withdrawable: MilliSatoshi = Field(..., alias="maxWithdrawable")
    default_description: str = Field("", alias="defaultDescription")

    @property
    def min_sats(self) -> int:
        return int(math.ceil(self.min_withdrawable / 1000))

    @property
    def max_sats(self) -> int:
        return int(math.floor(self.max_withdrawable / 1000))


class LndClient:
    def __init__(self, lnd_settings: LndSettings):
        self.settings = lnd_settings

    @cached_property
    def invoice_macaroon(self) -> str | None:
        macaroon_path = None
        if macaroon_path := self.settings.macaroon_by_path:
            pass
        elif network := self.settings.macaroon_by_network:
            macaroon_path = f'~/.lnd/data/chain/bitcoin/{network}/invoices.macaroon'
        if macaroon_path:
            with open(os.path.expanduser(macaroon_path), "rb") as f:
                return binascii.hexlify(f.read())

    async def query(self, method: str, api: str, data: dict = None, **kwargs) -> dict:
        async with self.request(api, method=method, json=data, **kwargs) as resp:
            results = [json.loads(line) async for line in resp.aiter_lines()]
            if len(results) == 1:
                return results[0]
            else:
                return results

    @asynccontextmanager
    async def request(self, api: str, method: str, **kwargs):
        async with httpx.AsyncClient(verify=self.settings.tls_cert or True) as client:
            url = f'{self.settings.url}{api}'
            logger.trace("request: %s %s %s", method, url, kwargs)
            if self.invoice_macaroon:
                kwargs['headers'] = {"Grpc-Metadata-macaroon": self.invoice_macaroon}
            async with client.stream(
                method=method,
                url=url,
                **kwargs,
            ) as resp:
                logger.trace("response: %s %s %d", method, url, resp.status_code)
                if not resp.is_success:
                    await resp.aread()
                resp.raise_for_status()
                yield resp

    @asynccontextmanager
    async def subscribe_to_invoices(self):
        async with self.subscribe('/v1/invoices/subscribe') as subscription:
            yield self.generate_invoices(subscription)

    @asynccontextmanager
    async def subscribe_to_invoice(self, r_hash: RequestHash):
        async with self.subscribe(f'/v2/invoices/subscribe/{r_hash.as_base64}') as subscription:
            yield self.generate_invoices(subscription)

    @asynccontextmanager
    async def subscribe(self, api: str, **request: dict) -> AsyncIterator[AsyncIterator[Invoice]]:
        logger.trace("subscribe %s %s", api, request)
        # FIXME: instead of this we should wait for a connection to be established, but httpx has no such event
        await self.check_ready()
        yield self.generate_events(api, request)

    async def generate_events(self, api: str, request: dict) -> AsyncIterator[Invoice]:
        # WORKAROUND: self.request(...) should be called inside subscribe() but
        # lnd does not return headers until the first event, so it deadlocks
        async with self.request(api, method='GET', json=request, timeout=None) as resp:
            async for line in resp.aiter_lines():
                logger.trace("subscribe line %s", line)
                yield json.loads(line)

    async def generate_invoices(self, event_generator):
        async for event in event_generator:
            yield Invoice(**event['result'])

    async def create_invoice(self, expiry: int = None, **kwargs) -> Invoice:
        await self.check_ready()
        resp = await self.query(
            'POST',
            '/v1/invoices',
            data=dict(
                **kwargs,
                expiry=expiry or self.settings.invoice_expiry,
                private=self.settings.private,
            ),
        )
        return Invoice(**resp)

    async def lookup_invoice(self, r_hash: RequestHash) -> Invoice | None:
        try:
            resp = await self.query("GET", f"/v1/invoice/{r_hash.as_hex}")
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                return None
            else:
                raise
        return Invoice(**resp)

    async def cancel_invoice(self, r_hash: RequestHash):
        """
        Only HODL invoices
        """
        await self.query("POST", "/v2/invoices/cancel", data=dict(payment_hash=r_hash.as_base64))

    async def pay_invoice(self, payment_request: PaymentRequest) -> PayInvoiceResult:
        await self.check_ready()
        try:
            decoded: LnAddr = payment_request.decode()
            logger.debug(f"Sending payment to {decoded}")
            results = await self.query(
                "POST",
                "/v2/router/send",
                data=dict(
                    payment_request=payment_request,
                    timeout_seconds=settings.withdraw_timeout,
                    fee_limit_sat=settings.fee_limit,
                ),
                timeout=httpx.Timeout(5, read=15),
            )
        except httpx.HTTPStatusError as exc:
            raise PayInvoiceError(exc.response.json()['error']['message']) from exc
        else:
            last_result = PayInvoiceResult(**results[-1]['result'])
            if last_result.status != 'SUCCEEDED':
                raise PayInvoiceError(last_result.failure_reason)
            return last_result

    async def query_state(self) -> State:
        resp = await self.query('GET', '/v1/state')
        return resp['state']

    async def query_info(self) -> dict:
        return await self.query('GET', '/v1/getinfo')

    async def check_ready(self):
        try:
            info: dict = await self.query_info()
        except httpx.HTTPStatusError as exc:
            raise LndIsNotReady(str(exc)) from exc
        else:
            is_ready = info['synced_to_chain'] is True and info['synced_to_graph'] is True and info['num_active_channels'] > 0
            if not is_ready:
                raise LndIsNotReady(info)


lnd = ContextualObject('lnd')


@as_task
async def monitor_invoices(lnd_client, db):
    while True:
        try:
            async with monitor_invoices_step(lnd_client, db) as task:
                await task
        except Exception as exc:
            logger.exception(f"Exception in monitor_invoices task: {exc}")
            await asyncio.sleep(5)


@as_task
@asynccontextmanager
async def monitor_invoices_step(lnd_client, db):
    logger.debug("Start monitoring invoices")
    # FIXME: monitor only invoices created by this web worker to avoid conflicts between workers
    try:
        async with lnd_client.subscribe_to_invoices() as subscription:
            logger.debug("Connected to LND")
            yield
            async for invoice in subscription:
                logger.trace("monitor_invoices %s", invoice)
                if invoice.state == 'SETTLED':
                    logger.debug("donation paid %s", invoice)
                    try:
                        # Try to lock donation multiple times
                        while True:
                            async with db.session() as db_session:
                                donations_db = DonationsDbLib(db_session)
                                try:
                                    donation: Donation = await donations_db.lock_donation(r_hash=invoice.r_hash)
                                except sqlalchemy.exc.DBAPIError as exc:
                                    # could not serialize access due to concurrent update
                                    if isinstance(exc.__cause__.__cause__, asyncpg.exceptions.SerializationError):
                                        # Just try again
                                        continue
                                    else:
                                        raise
                                if donation.paid_at is not None:
                                    logger.warning("Donation %s was already paid, skipping", donation)
                                else:
                                    await donation_paid(
                                        db_session,
                                        donation=donation,
                                        paid_at=invoice.settle_date,
                                        amount=invoice.amt_paid_sat,
                                    )
                                break
                    except Exception:
                        logger.exception("Error while handling donation notification from lnd")
    finally:
        logger.debug("Stopped monitoring invoices")


@register_app_command
async def pay_withdraw_request(lnurl: str):
    decoded_url = _lnurl_decode(lnurl)
    logger.debug("decoded lnurl: %s", decoded_url)
    async with httpx.AsyncClient() as client:
        lnurl_response = await client.get(decoded_url)
        lnurl_data = LnurlWithdrawResponse(**lnurl_response.json())
        logger.debug("received response: %s", lnurl_data)
        lnd = LndClient(settings.lnd)
        invoice: Invoice = await lnd.create_invoice(
            memo=lnurl_data.default_description,
            value=lnurl_data.max_sats,
        )
        await client.get(lnurl_data.callback, params=dict(k1=lnurl_data.k1, pr=invoice.payment_request))


def svg_to_png(svg_data: bytes) -> bytes:
    from cairosvg import svg2png
    return svg2png(svg_data)


def lightning_payment_metadata(receiver: Donator | SocialAccount) -> str:
    fields = [
        ("text/identifier", receiver.lightning_address),
        ("text/plain", f"Tip for {receiver.unique_name} [{receiver.id}]"),
    ]
    prefix = 'data:image/svg+xml;base64,'
    if receiver.avatar_url.startswith(prefix):
        svg_base64_data: str = receiver.avatar_url[len(prefix):]
        if settings.lnurlp.enable_svg_images:
            fields.append(("image/svg+xml;base64", svg_base64_data))
        else:
            svg_data: bytes = from_base64(svg_base64_data)
            png_data = svg_to_png(svg_data)
            fields.append(("image/png;base64", to_base64(png_data)))
    return json.dumps(fields)
