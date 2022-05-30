import binascii
import os.path
import json
import logging
from typing import Any
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel

from .settings import settings
from .core import hex_to_base64

logger = logging.getLogger(__name__)


def load_invoice_macaroon() -> str:
    return binascii.hexlify(open(os.path.expanduser("~/.lnd/data/chain/bitcoin/mainnet/invoices.macaroon"), "rb").read())


Data = dict[str, Any]


async def query_lnd(method: str, api: str, **request: Data) -> Data:
    async with request_lnd(api, method=method, json=request) as resp:
        return resp.json()


@asynccontextmanager
async def request_lnd(api: str, **kwargs):
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            url=f'{settings().lnd_url}{api}',
            headers={"Grpc-Metadata-macaroon": load_invoice_macaroon()},
            **kwargs,
        )
        resp.raise_for_status()
        yield resp


async def subscribe_lnd(api: str, **request: Data):
    async with request_lnd(api, method='GET', json=request, timeout=None) as resp:
        async for line in resp.aiter_lines():
            yield json.loads(line)


class Invoice(BaseModel):
    r_hash: str
    payment_request: str
    amount: int


async def create_invoice(memo: str, amount: int) -> Invoice:
    resp = await query_lnd('POST', '/v1/invoices', memo=memo, value=amount)
    return Invoice(amount=amount, **resp)


async def cancel_invoice(r_hash: str):
    await query_lnd("POST", "/v2/invoices/cancel", payment_hash=hex_to_base64(r_hash))


async def monitor_invoices(db):
    async for data in subscribe_lnd("/v1/invoices/subscribe"):
        logger.debug(f"monitor_invoices {data}")
        result = data['result']
        if result['state'] == 'SETTLED':
            logger.debug(f"donation paid {data}")
            async with db.acquire_session() as db_session:
                await db_session.donation_paid(
                    r_hash=result['r_hash'],
                    paid_at=result['settled_date'],
                    amount=result['amt_paid_sat'],
                )

State = str


async def query_state() -> State:
    resp = await query_lnd('GET', '/v1/state')
    return resp['state']
