import re
import io
from base64 import b64encode
from urllib.parse import urlparse

import qrcode
from fastapi import Request
from email_validator import validate_email
from qrcode.image.pure import PymagingImage

from .youtube import validate_youtube_url
from .types import UnsupportedTarget, Url, PaymentRequest


async def get_db_session(request: Request):
    async with request.app.db.session() as session:
        yield session


async def get_lnd(request: Request):
    return request.app.lnd


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
