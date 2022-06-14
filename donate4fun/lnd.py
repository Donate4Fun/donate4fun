import binascii
import asyncio
import os.path
import json
import logging
from functools import cached_property
from typing import Any
from contextlib import asynccontextmanager

import anyio
import httpx
from anyio import TASK_STATUS_IGNORED
from anyio.abc import TaskStatus

from .settings import LndSettings
from .types import RequestHash, PaymentRequest
from .models import Invoice

logger = logging.getLogger(__name__)


Data = dict[str, Any]
State = str


class PayInvoiceError(Exception):
    pass


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
        async with httpx.AsyncClient() as client:
            url = f'{self.settings.url}{api}'
            logger.debug(f"{method} {url}")
            if self.invoice_macaroon:
                kwargs['headers'] = {"Grpc-Metadata-macaroon": self.invoice_macaroon}
            async with client.stream(
                method=method,
                url=url,
                **kwargs,
            ) as resp:
                logger.debug(f"{method} {url} {resp.status_code}")
                if not resp.is_success:
                    await resp.aread()
                resp.raise_for_status()
                yield resp

    async def subscribe(self, api: str, **request: Data):
        # WORKAROUND: This should be after the request but
        # lnd does not return headers until the first event, so it deadlocks

        async def request_impl(queue):
            async with self.request(api, method='GET', json=request, timeout=None) as resp:
                async for line in resp.aiter_lines():
                    await queue.put(json.loads(line))

        async with anyio.create_task_group() as tg:
            queue = asyncio.Queue()
            tg.start_soon(request_impl, queue)
            await asyncio.sleep(0.2)
            yield
            while result := await queue.get():
                yield result

    async def create_invoice(self, memo: str, value: int) -> Invoice:
        resp = await self.query(
            'POST',
            '/v1/invoices',
            data=dict(
                memo=memo,
                value=value,
                expiry=self.settings.invoice_expiry,
                private=self.settings.private,
            ),
        )
        return Invoice(value=value, **resp)

    async def lookup_invoice(self, r_hash: RequestHash) -> Invoice:
        resp = await self.query("GET", f"/v1/invoice/{r_hash.as_hex}")
        return Invoice(**resp)

    async def cancel_invoice(self, r_hash: RequestHash):
        """
        Only HODL invoices
        """
        await self.query("POST", "/v2/invoices/cancel", data=dict(payment_hash=r_hash.as_hex))

    async def pay_invoice(self, payment_request: PaymentRequest, timeout: int):
        results = await self.query(
            "POST",
            "/v2/router/send",
            data=dict(payment_request=payment_request, timeout_seconds=timeout),
            timeout=httpx.Timeout(5, read=10),
        )
        last_result = results[-1]
        if last_result['result']['status'] != 'SUCCEEDED':
            raise PayInvoiceError(json.dumps(last_result))

    async def query_state(self) -> State:
        resp = await self.query('GET', '/v1/state')
        return resp['state']


async def monitor_invoices_loop(lnd_client, db):
    while True:
        try:
            await monitor_invoices(lnd_client, db)
        except Exception as exc:
            logger.error(f"Exception in monitor_invoices task: {exc}")
            await asyncio.sleep(5)


async def monitor_invoices(lnd_client, db, *, task_status: TaskStatus = TASK_STATUS_IGNORED):
    logger.debug("Start monitoring invoices")
    async for data in lnd_client.subscribe("/v1/invoices/subscribe"):
        logger.debug(f"monitor_invoices {data}")
        if data is None:
            task_status.started()
            continue
        invoice: Invoice = Invoice(**data['result'])
        if invoice.state == 'SETTLED':
            logger.debug(f"donation paid {data}")
            try:
                async with db.session() as sess:
                    await sess.donation_paid(
                        r_hash=invoice.r_hash,
                        paid_at=invoice.settle_date,
                        amount=invoice.amt_paid_sat,
                    )
            except Exception:
                logger.exception("Error while handling donation notification from lnd")
