import binascii
import asyncio
import os.path
import json
import logging
from functools import cached_property
from typing import Any
from contextlib import asynccontextmanager
from datetime import datetime

import anyio
import httpx
from pydantic import BaseModel
from anyio import TASK_STATUS_IGNORED
from anyio.abc import TaskStatus

from .settings import LndSettings
from .core import base64_to_hex
from .types import RequestHash, PaymentRequest

logger = logging.getLogger(__name__)


Data = dict[str, Any]
State = str


class Invoice(BaseModel):
    r_hash: str
    payment_request: str
    amount: int


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

    async def query(self, method: str, api: str, **request: Data) -> Data:
        async with self.request(api, method=method, json=request) as resp:
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

    async def create_invoice(self, memo: str, amount: int) -> Invoice:
        resp = await self.query(
            'POST',
            '/v1/invoices',
            memo=memo,
            value=amount,
            expiry=self.settings.invoice_expiry,
            private=self.settings.private,
        )
        return Invoice(amount=amount, **resp)

    async def cancel_invoice(self, r_hash: RequestHash):
        await self.query("POST", "/v2/invoices/cancel", payment_hash=base64_to_hex(r_hash))

    async def pay_invoice(self, payment_request: PaymentRequest, timeout: int):
        results = await self.query("POST", "/v2/router/send", payment_request=payment_request, timeout_seconds=timeout)
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
        result = data['result']
        if result['state'] == 'SETTLED':
            logger.debug(f"donation paid {data}")
            try:
                async with db.session() as sess:
                    await sess.donation_paid(
                        r_hash=result['r_hash'],
                        paid_at=datetime.fromtimestamp(int(result['settle_date'])),
                        amount=int(result['amt_paid_sat']),
                    )
            except Exception:
                logger.exception("Error while handling donation notification from lnd")
