import binascii
import asyncio
import os.path
import json
import logging
import math
from functools import cached_property
from typing import Any, Literal
from contextlib import asynccontextmanager

import httpx
from lnpayencode import LnAddr
from lnurl.helpers import _lnurl_decode
from lnurl.models import LnurlResponseModel
from lnurl.types import MilliSatoshi
from pydantic import Field, AnyUrl

from .settings import LndSettings, settings
from .types import RequestHash, PaymentRequest
from .models import Invoice, Donator, PayInvoiceResult
from .core import as_task, register_command, ContextualObject
from .api_utils import track_donation

logger = logging.getLogger(__name__)


Data = dict[str, Any]
State = str


class PayInvoiceError(Exception):
    pass


class LndIsNotReady(Exception):
    pass


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
            return binascii.hexlify(open(os.path.expanduser(macaroon_path), "rb").read())

    async def query(self, method: str, api: str, data: Data = None, **kwargs) -> Data:
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
                logger.debug("response: %s %s %d", method, url, resp.status_code)
                if not resp.is_success:
                    await resp.aread()
                resp.raise_for_status()
                yield resp

    async def subscribe(self, api: str, **request: Data):
        # WORKAROUND: This should be after the request but
        # lnd does not return headers until the first event, so it deadlocks
        logger.trace("subscribe %s %s", api, request)

        @as_task
        @asynccontextmanager
        async def request_impl(queue):
            # FIXME: instead of this we should wait for a connection to be established, but httpx has no such event
            await self.query_info()
            yield
            async with self.request(api, method='GET', json=request, timeout=None) as resp:
                async for line in resp.aiter_lines():
                    logger.trace("subscribe line %s", line)
                    await queue.put(json.loads(line))

        queue = asyncio.Queue()
        async with request_impl(queue):
            # FIXME: instead of this we should wait for a connection to be established, but httpx has no such event
            await asyncio.sleep(0.2)
            yield
            while result := await queue.get():
                yield result

    async def create_invoice(self, **kwargs) -> Invoice:
        await self.ensure_ready()
        resp = await self.query(
            'POST',
            '/v1/invoices',
            data=dict(
                **kwargs,
                expiry=self.settings.invoice_expiry,
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
        await self.ensure_ready()
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

    async def query_info(self):
        return await self.query('GET', '/v1/getinfo')

    async def ensure_ready(self):
        info = await lnd.query_info()
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
        async for data in lnd_client.subscribe("/v1/invoices/subscribe"):
            if data is None:
                logger.debug("Connected to LND")
                yield
                continue
            logger.debug("monitor_invoices %s", data)
            invoice: Invoice = Invoice(**data['result'])
            if invoice.state == 'SETTLED':
                logger.debug(f"donation paid {data}")
                try:
                    async with db.session() as sess:
                        donation = await sess.lock_donation(r_hash=invoice.r_hash)
                        track_donation(donation)
                        await sess.donation_paid(
                            donation_id=donation.id,
                            paid_at=invoice.settle_date,
                            amount=invoice.amt_paid_sat,
                        )
                except Exception:
                    logger.exception("Error while handling donation notification from lnd")
    finally:
        logger.debug("Stopped monitoring invoices")


@register_command
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


def lightning_payment_metadata(receiver: Donator):
    return json.dumps([
        ("text/identifier", str(receiver.id)),
        ("text/plain", f"Sats for {receiver.name}"),
    ])
