import io
from base64 import b64encode

import qrcode
from fastapi import Request, WebSocket
from qrcode.image.pure import PymagingImage

from .types import PaymentRequest


async def get_db_session(request: Request):
    async with request.app.db.session() as session:
        yield session


async def get_db(request: Request):
    return request.app.db


async def get_lnd(request: Request):
    return request.app.lnd


async def get_pubsub(websocket: WebSocket):
    return websocket.app.pubsub


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
