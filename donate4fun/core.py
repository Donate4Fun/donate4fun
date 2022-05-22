import re
import io
import binascii
import os.path
from base64 import b64encode
from urllib.parse import urlparse
from typing import Any

import qrcode
import httpx
from email_validator import validate_email
from qrcode.image.pure import PymagingImage

from .youtube import validate_youtube_url
from .settings import settings
from .models import UnsupportedTarget, Url

PaymentRequest = str


async def validate_target(target: str):
    if re.match(r'https?://.+', target):
        return await validate_target_url(target)
    return validate_email(target).email


async def validate_target_url(target: Url):
    parsed = urlparse(target)
    if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be']:
        return await validate_youtube_url(parsed)
    else:
        raise UnsupportedTarget


def datauri(pay_req: PaymentRequest):
    """
    converts ln payment request to qr code in form of data: uri
    """
    img = qrcode.make(pay_req, image_factory=PymagingImage)
    data = io.BytesIO()
    img.save(data)
    encoded = b64encode(data.getvalue()).decode()
    return 'data:image/png;base64,' + encoded


def load_invoice_macaroon() -> str:
    return binascii.hexlify(open(os.path.expanduser("~/.lnd/data/chain/bitcoin/mainnet/invoices.macaroon"), "rb").read())


async def query_lnd(method: str, api: str, **request: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=method,
            url=f'{settings().lnd_url}{api}',
            json=request,
            headers={"Grpc-Metadata-macaroon": load_invoice_macaroon()},
        )
        return resp.json()
