import json
from datetime import datetime

import httpx
import posthog
from lnpayencode import LnAddr

from .models import Donation, PaymentRequest, Donator, SocialAccountOwned
from .db import DbSession
from .db_libs import TwitterDbLib, YoutubeDbLib, GithubDbLib, DonationsDbLib
from .types import LnurlpError, RequestHash, Satoshi, MilliSatoshi
from .api_utils import load_donator, HttpClient, sha256hash


async def init_donation(db_session: DbSession, donation: Donation, expiry: int = None) -> (PaymentRequest, Donation):
    """
    Takes pre-filled Donation object and do one of the following:
         - if receiver is a Donate4.Fun account and sender has enough balance then just transfers money without lightning
         - if receiver has a lightning address and sender has enough money then pays from balance to a lightning address
         - if receiver has no lightning address (just a social account) then transfers money from sender balance
           or create a payment request to send money from a lightning wallet
    """
    from .lnd import lnd, Invoice, PayInvoiceResult
    donator = await load_donator(db_session, donation.donator.id)
    # If donator has enough money (and not fulfilling his own balance) - try to pay donation instantly
    use_balance = (
        (donation.receiver and donation.receiver.id) != donator.id
        and (donator.available_balance if donation.lightning_address else donator.balance) >= donation.amount
    )
    if donation.lightning_address:
        # Payment to a lnurlp - check that it works and we can pay later, but we will fetch invoice again
        output_pay_req: PaymentRequest = await fetch_lightning_address(donation)
        donation.output_r_hash = RequestHash(pay_req.decode().paymenthash)
    donations_db = DonationsDbLib(db_session)
    await donations_db.create_donation(donation)
    if use_balance:
        return None, await finish_donation(db_session, donation, amount=donation.amount, paid_at=donation.created_at)
    else:
        # Payment by invoice
        invoice: Invoice = await lnd.create_invoice(memo=make_memo(donation), value=donation.amount, expiry=expiry)
        donation.r_hash = invoice.r_hash  # Save this hash to finish the donation after the payment
        return invoice.payment_request, donation


async def finish_donation(
    db_session: DbSession, donation: Donation, amount: Satoshi, paid_at: datetime,
    fee_msat: MilliSatoshi = 0, claimed_at: datetime = None,
) -> Donation:
    """
    At the end money from social accounts are automatically transferred to linked Donate4.Fun account if they exist.
    """
    if donation.lightning_address:
        pay_req: PaymentRequest = await fetch_lightning_address(donation)
        pay_result: PayInvoiceResult = await lnd.pay_invoice(pay_req)
        amount = pay_result.value_sat
        paid_at = pay_result.creation_date
        fee_msat = pay_result.fee_msat
        claimed_at = pay_result.creation_date

    donations_db = DonationsDbLib(db_session)
    await donations_db.donation_paid(
        donation_id=donation.id, amount=amount, paid_at=paid_at, fee_msat=fee_msat, claimed_at=claimed_at,
    )
    await auto_transfer_donations(db_session, donation)
    # Reload donation with a fresh state
    donation = await donations_db.query_donation(id=donation.id)
    track_donation(donation)
    return donation


async def auto_transfer_donations(db: DbSession, donation: Donation) -> int:
    """
    Returns sats amount transferred
    """
    if donation.youtube_channel:
        social_db = YoutubeDbLib(db)
    elif donation.twitter_account:
        social_db = TwitterDbLib(db)
    elif donation.github_user:
        social_db = GithubDbLib(db)
    else:
        social_db = None

    if social_db:
        account = getattr(donation, social_db.donation_field)
        if not isinstance(account, social_db.owned_model):
            account: SocialAccountOwned = await social_db.query_account(id=account.id)
        if account.lightning_address:
            pay_req: PaymentRequest = await fetch_lightning_address(donation)
            r_hash = RequestHash(pay_req.decode().paymenthash)
        if account.owner_id is not None:
            return await social_db.transfer_donations(account, Donator(id=account.owner_id))
    return 0


def lightning_address_to_lnurlp(address: str) -> str:
    name, host = address.split('@', 1)
    return f'https://{host}/.well-known/lnurlp/{name}'


class LnurlpClient(HttpClient):
    async def fetch_metadata(self, lnurlp: str) -> dict:
        try:
            response = await self.get(lnurlp, follow_redirects=True)
        except httpx.HTTPStatusError as exc:
            raise LnurlpError(f"{exc.request.url} responded with {exc.response.status_code}: {exc.response.content}") from exc
        except httpx.HTTPError as exc:
            raise LnurlpError(f"HTTP error with {exc.request.url}: {exc}") from exc
        metadata = response.json()
        # https://github.com/lnurl/luds/blob/luds/06.md
        if metadata.get('status', 'OK') != 'OK':
            raise LnurlpError(f"Status is not OK: {metadata}")
        return metadata

    async def fetch_invoice(self, metadata: dict, amount: Satoshi, name: str, comment: str) -> PaymentRequest:
        if not metadata['minSendable'] <= amount * 1000 <= metadata['maxSendable']:
            raise LnurlpError(f"Amount is out of bounds: {amount} {metadata}")
        params = dict(amount=amount * 1000)
        if payerdata_request := metadata.get('payerData'):
            payerdata = {}
            if 'name' in payerdata_request:
                payerdata['name'] = f'{name} via Donate4.Fun'
            # Separators are important for hashes to match
            params['payerdata'] = json.dumps(payerdata, separators=(',', ':'))
        if 'commentAllowed' in metadata:
            params['comment'] = comment[:metadata['commentAllowed']]
        try:
            response = await self.get(metadata['callback'], params=params)
        except httpx.HTTPStatusError as exc:
            raise LnurlpError(f"Callback responded with {exc}: {exc.response.content}") from exc
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
        if invoice_amount != amount:
            raise LnurlpError(f"Amount in invoice does not match requested amount: {invoice_amount} != {amount}")
        return pay_req


def get_lnurlp_name(donation: Donation) -> str:
    if donation.donator_twitter_account:
        return '@' + donation.donator_twitter_account.handle
    else:
        return donation.donator.name


def get_lnurlp_comment(donation: Donation, name: str) -> str:
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
    return f'Tip from {name} via Donate4.Fun for {target}'


async def fetch_lightning_address(donation: Donation) -> PaymentRequest:
    async with LnurlpClient() as client:
        metadata: dict = await client.fetch_metadata(lightning_address_to_lnurlp(donation.lightning_address))
        fields = dict(json.loads(metadata['metadata']))
        name: str = get_lnurlp_name(donation)
        pay_req = await client.fetch_invoice(
            metadata,
            amount=donation.amount,
            name=f'{name} via Donate4.Fun',
            comment=get_lnurlp_comment(donation, name),
        )
        return pay_req


def make_memo(donation: Donation) -> str:
    if account := donation.receiver_social_account:
        return f"Tip for {account.unique_name} via Donate4.Fun"
    elif donation.receiver:
        if donation.receiver.id == donation.donator.id:
            return f"[Donate4.fun] fulfillment for {donation.receiver.name}"
        else:
            return f"[Donate4.fun] donation to {donation.receiver.name}"
    else:
        raise ValueError(f"Could not make a memo for donation {donation}")


def track_donation(donation: Donation):
    if donation.twitter_account:
        target_type = 'twitter'
    elif donation.youtube_channel:
        target_type = 'youtube'
    elif donation.receiver:
        target_type = 'donate4fun'
    else:
        target_type = 'unknown'
    if donation.lightning_address:
        via = 'lightning-address'
    else:
        via = 'donate4fun'
    donator_id = donation.donator and donation.donator.id
    posthog.capture(donator_id, 'donation-paid', dict(amount=donation.amount, target_type=target_type, via=via))
