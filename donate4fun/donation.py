import json
from datetime import datetime

import httpx
from lnpayencode import LnAddr

from .models import Donation, PaymentRequest, Invoice, PayInvoiceResult
from .db import DbSession
from .db_donations import DonationsDbLib
from .types import LnurlpError, RequestHash
from .api_utils import load_donator, auto_transfer_donations, track_donation, HttpClient, sha256hash

from .lnd import lnd


async def donate(donation: Donation, db_session: DbSession, expiry: int = None) -> (PaymentRequest, Donation):
    donator = await load_donator(db_session, donation.donator.id)
    # If donator has enough money (and not fulfilling his own balance) - try to pay donation instantly
    use_balance = (
        (donation.receiver and donation.receiver.id) != donator.id
        and (donator.available_balance if donation.lightning_address else donator.balance) >= donation.amount
    )
    if donation.lightning_address:
        # Payment to a lnurlp
        pay_req: PaymentRequest = await fetch_lightning_address(donation)
        r_hash = RequestHash(pay_req.decode().paymenthash)
        if use_balance:
            # FIXME: this leads to 'duplicate key value violates unique constraint "donation_rhash_key"'
            # if we are donating to a local lightning address
            donation.r_hash = r_hash
        else:
            donation.transient_r_hash = r_hash
    elif not use_balance:
        # Payment by invoice
        invoice: Invoice = await lnd.create_invoice(memo=make_memo(donation), value=donation.amount, expiry=expiry)
        donation.r_hash = invoice.r_hash  # This hash is needed to find and complete donation after payment succeeds
        pay_req = invoice.payment_request
    else:
        # Fully internal payment
        pay_req = None
    donations_db = DonationsDbLib(db_session)
    await donations_db.create_donation(donation)
    if use_balance:
        if donation.lightning_address:
            pay_result: PayInvoiceResult = await lnd.pay_invoice(pay_req)
            amount = pay_result.value_sat
            paid_at = pay_result.creation_date
            fee_msat = pay_result.fee_msat
            claimed_at = pay_result.creation_date
            pay_req = None  # We should not return pay_req to client because it's already paid
        else:
            amount = donation.amount
            paid_at = datetime.utcnow()
            fee_msat = None
            claimed_at = None
        await donations_db.donation_paid(
            donation_id=donation.id, amount=amount, paid_at=paid_at, fee_msat=fee_msat, claimed_at=claimed_at,
        )
        await auto_transfer_donations(db_session, donation)
        # Reload donation with a fresh state
        donation = await donations_db.query_donation(id=donation.id)
        track_donation(donation)
    return pay_req, donation


async def fetch_lightning_address(donation: Donation) -> PaymentRequest:
    name, host = donation.lightning_address.split('@', 1)
    async with HttpClient() as client:
        try:
            response = await client.get(f'https://{host}/.well-known/lnurlp/{name}', follow_redirects=True)
        except httpx.HTTPStatusError as exc:
            raise LnurlpError(f"{exc.request.url} responded with {exc.response.status_code}: {exc.response.content}") from exc
        except httpx.HTTPError as exc:
            raise LnurlpError(f"HTTP error with {exc.request.url}: {exc}") from exc
        metadata = response.json()
        # https://github.com/lnurl/luds/blob/luds/06.md
        if metadata.get('status', 'OK') != 'OK':
            raise LnurlpError(f"Status is not OK: {metadata}")
        if not metadata['minSendable'] <= donation.amount * 1000 <= metadata['maxSendable']:
            raise LnurlpError(f"Amount is out of bounds: {donation.amount} {metadata}")
        fields = dict(json.loads(metadata['metadata']))
        if donation.donator_twitter_account:
            name = '@' + donation.donator_twitter_account.handle
        else:
            name = donation.donator.name
        params = dict(amount=donation.amount * 1000)
        if payerdata_request := metadata.get('payerData'):
            payerdata = {}
            if 'name' in payerdata_request:
                payerdata['name'] = f'{name} via Donate4.Fun'
            # Separators are important for hashes to match
            params['payerdata'] = json.dumps(payerdata, separators=(',', ':'))
        if donation.youtube_video:
            target = f'https://youtube.com/watch?v={donation.youtube_video.video_id}'
        elif donation.twitter_tweet:
            target = f'https://twitter.com/{donation.twitter_account.handle}/status/{donation.twitter_tweet.tweet_id}'
        elif donation.youtube_channel:
            target = f'https://youtube.com/channel/{donation.youtube_channel.channel_id}'
        elif donation.twitter_account:
            target = f'https://twitter.com/{donation.twitter_account.handle}'
        elif donation.lightning_address:
            target = fields.get('text/identifier', donation.lightning_address)
        comment = f'Tip from {name} via Donate4.Fun for {target}'
        if 'commentAllowed' in metadata:
            params['comment'] = comment[:metadata['commentAllowed']]
        try:
            response = await client.get(metadata['callback'], params=params)
        except httpx.HTTPStatusError as exc:
            raise LnurlpError(f"Callback responded with {exc}: {response.content}") from exc
        except httpx.HTTPError as exc:
            raise LnurlpError(f"Callback responded with {exc}") from exc
        data = response.json()
        if data.get('status', 'OK') != 'OK':
            raise LnurlpError(f"Status is not OK: {data}")
        pay_req = PaymentRequest(data['pr'])
        invoice: LnAddr = pay_req.decode()
        expected_hash = dict(invoice.tags)['h']
        # https://github.com/lnurl/luds/blob/luds/18.md#3-committing-payer-to-the-invoice
        full_metadata: str = metadata['metadata'] + params.get('payerdata', '')
        if sha256hash(full_metadata) != expected_hash:
            raise LnurlpError(f"Metadata hash does not match invoice hash: sha256({full_metadata}) != {expected_hash}")
        invoice_amount = invoice.amount * 10 ** 8
        if invoice_amount != donation.amount:
            raise LnurlpError(f"Amount in invoice does not match requested amount: {invoice_amount} != {donation.amount}")
        return pay_req


def make_memo(donation: Donation) -> str:
    if account := donation.receiver_social_account:
        return f"Donate4.Fun donation to {account.unique_name}"
    elif donation.receiver:
        if donation.receiver.id == donation.donator.id:
            return f"[Donate4.fun] fulfillment for {donation.receiver.name}"
        else:
            return f"[Donate4.fun] donation to {donation.receiver.name}"
    else:
        raise ValueError(f"Could not make a memo for donation {donation}")
