import re
import io
from binascii import a2b_hex, b2a_hex
from base64 import b64encode, b64decode, urlsafe_b64encode
from urllib.parse import urlparse

import qrcode
from fastapi import Request
from email_validator import validate_email
from qrcode.image.pure import PymagingImage

from .youtube import validate_youtube_url
from .types import UnsupportedTarget, Url

PaymentRequest = str


async def get_db_session(request: Request):
    async with request.app.db.acquire_session() as session:
        yield session


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


def payreq_to_datauri(pay_req: PaymentRequest):
    """
    converts ln payment request to qr code in form of data: uri
    """
    img = qrcode.make(pay_req, image_factory=PymagingImage)
    data = io.BytesIO()
    img.save(data)
    return to_datauri('image/png', data.getvalue())


def to_datauri(mime_type: str, data: bytes) -> str:
    encoded = b64encode(data).decode()
    return f'data:{mime_type};base64,{encoded}'


def hex_to_base64(r_hash: str):
    return urlsafe_b64encode(a2b_hex(r_hash)).decode()


def base64_to_hex(r_hash: str):
    return b2a_hex(b64decode(r_hash)).decode()
