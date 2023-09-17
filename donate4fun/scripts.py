import httpx
import yaml
from lnurl.helpers import _lnurl_decode

from .lnd import LnurlWithdrawResponse, Invoice
from .types import PaymentRequest
from .dev_helpers import get_carol_lnd
from .api_utils import register_app_command


@register_app_command
async def withdraw(lnurl: str):
    payer_lnd = get_carol_lnd()
    decoded_url = _lnurl_decode(lnurl)
    async with httpx.AsyncClient() as client:
        lnurl_response = await client.get(decoded_url)
        lnurl_response.raise_for_status()
        lnurl_data = LnurlWithdrawResponse(**lnurl_response.json())
        invoice: Invoice = await payer_lnd.create_invoice(
            memo=lnurl_data.default_description,
            value=lnurl_data.max_sats,
        )
        callback_response = await client.get(lnurl_data.callback, params=dict(k1=lnurl_data.k1, pr=invoice.payment_request))
        callback_response.raise_for_status()
        print(yaml.dump(callback_response.json()))


@register_app_command
async def pay(lnurl: str):
    payer_lnd = get_carol_lnd()
    result = await payer_lnd.pay_invoice(PaymentRequest(lnurl))
    print(yaml.dump(result.dict()))
