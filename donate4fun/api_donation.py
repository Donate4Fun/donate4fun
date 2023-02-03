import json
import logging
import hashlib
from uuid import UUID
from datetime import datetime

import httpx
from fastapi import Request, Depends, HTTPException, APIRouter
from sqlalchemy import select
from lnpayencode import LnAddr

from .models import (
    Donation, Donator, Invoice, DonateResponse, DonateRequest,
    DonationPaidRequest, PayInvoiceResult, PaymentRequest, RequestHash
)
from .types import ValidationError, LnurlpError
from .api_utils import (
    get_donator, get_db_session, load_donator, auto_transfer_donations, track_donation, HttpClient, get_donations_db, only_me,
    sha256hash, get_social_provider_db,
)
from .db_libs import GithubDbLib, TwitterDbLib, YoutubeDbLib, DonationsDbLib
from .db_donations import sent_donations_subquery, received_donations_subquery
from .db_models import DonationDb
from .db_social import SocialDbWrapper
from .twitter import query_or_fetch_twitter_account
from .donatees import apply_target
from .lnd import lnd
from .settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.post("/donate", response_model=DonateResponse)
async def donate(
    web_request: Request, request: DonateRequest, donator: Donator = Depends(get_donator), db_session=Depends(get_db_session),
 ) -> DonateResponse:
    logger.debug(
        "Donator %s wants to donate %d to %s",
        donator.id, request.amount, request.target or request.channel_id or request.lightning_address,
    )
    donation = Donation(
        amount=request.amount,
        donator=donator,
    )
    if request.lightning_address:
        donation.lightning_address = request.lightning_address
    if request.receiver_id:
        # Donation to a donator - possibly just an own balance fulfillment
        receiver = await load_donator(db_session, request.receiver_id)
        if not receiver.connected:
            raise ValidationError("Money receiver should have a connected wallet")
        donation.receiver = receiver
    elif request.social_account_id and request.social_provider:
        db_lib: SocialDbWrapper = get_social_provider_db(request.social_provider)
        social_account = await db_lib(db_session).query_account(id=request.social_account_id)
        setattr(donation, db_lib.donation_field, social_account)
        donation.lightning_address = donation.lightning_address or social_account.lightning_address
    elif request.target:
        await apply_target(donation, request.target, db_session)
    # FIXME: the following elif blocks are deprecated
    elif request.channel_id:
        donation.youtube_channel = await YoutubeDbLib(db_session).query_account(id=request.channel_id)
        donation.lightning_address = donation.youtube_channel.lightning_address
    elif request.twitter_account_id:
        donation.twitter_account = await TwitterDbLib(db_session).query_account(id=request.twitter_account_id)
        donation.lightning_address = donation.twitter_account.lightning_address
    elif request.github_user_id:
        donation.github_user = await GithubDbLib(db_session).query_account(id=request.github_user_id)
        donation.lightning_address = donation.github_user.lightning_address
    else:
        raise ValidationError("donation should have a target, channel_id or receiver_id")
    if request.donator_twitter_handle:
        donation.donator_twitter_account = await query_or_fetch_twitter_account(
            db=TwitterDbLib(db_session), handle=request.donator_twitter_handle,
        )
    donator = await load_donator(db_session, donator.id)
    # If donator has enough money (and not fulfilling his own balance) - try to pay donation instantly
    use_balance = (
        request.receiver_id != donator.id
        and (donator.available_balance if donation.lightning_address else donator.balance) >= request.amount
    )
    if donation.lightning_address:
        pay_req: PaymentRequest = await fetch_lightning_address(donation)
        r_hash = RequestHash(pay_req.decode().paymenthash)
        if use_balance:
            # FIXME: this leads to 'duplicate key value violates unique constraint "donation_rhash_key"'
            # if we are donating to a local lightning address
            donation.r_hash = r_hash
        else:
            donation.transient_r_hash = r_hash
    elif not use_balance:
        invoice: Invoice = await lnd.create_invoice(memo=make_memo(donation), value=request.amount)
        donation.r_hash = invoice.r_hash  # This hash is needed to find and complete donation after payment succeeds
        pay_req = invoice.payment_request
    donations_db = DonationsDbLib(db_session)
    await donations_db.create_donation(donation)
    if use_balance:
        if donation.lightning_address:
            pay_result: PayInvoiceResult = await lnd.pay_invoice(pay_req)
            amount = pay_result.value_sat
            paid_at = pay_result.creation_date
            fee_msat = pay_result.fee_msat
            claimed_at = pay_result.creation_date
        else:
            amount = request.amount
            paid_at = datetime.utcnow()
            fee_msat = None
            claimed_at = None
        await donations_db.donation_paid(
            donation_id=donation.id, amount=amount, paid_at=paid_at, fee_msat=fee_msat, claimed_at=claimed_at,
        )
        await auto_transfer_donations(db_session, donation)
        # Reload donation with a fresh state
        donation = await donations_db.query_donation(id=donation.id)
        # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
        web_request.session['balance'] = (await db_session.query_donator(id=donator.id)).balance
        track_donation(donation)
        return DonateResponse(donation=donation, payment_request=None)
    else:
        return DonateResponse(donation=donation, payment_request=pay_req)


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
            raise LnurlpError(response.content) from exc
        except httpx.HTTPError as exc:
            raise LnurlpError(exc) from exc
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


@router.get("/donation/{donation_id}", response_model=DonateResponse)
async def get_donation(donation_id: UUID, db_session=Depends(get_donations_db)):
    donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.lookup_invoice(donation.r_hash)
        if invoice is None or invoice.state == 'CANCELED':
            logger.debug(f"Invoice {invoice} cancelled, recreating")
            invoice = await lnd.create_invoice(memo=make_memo(donation), value=donation.amount)
            await db_session.update_donation(donation_id=donation_id, r_hash=invoice.r_hash)
        payment_request = invoice.payment_request
    else:
        payment_request = None
    return DonateResponse(donation=donation, payment_request=payment_request)


@router.post("/donation/{donation_id}/paid", response_model=Donation)
async def donation_paid(donation_id: UUID, request: DonationPaidRequest, db=Depends(get_donations_db)):
    donation: Donation = await db.query_donation(id=donation_id)
    if donation.lightning_address is None:
        # Do nothing for all other cases
        return
    digest = RequestHash(hashlib.sha256(bytes.fromhex(request.preimage)).digest())
    if digest != donation.transient_r_hash:
        raise ValidationError(f"Preimage hash does not match {digest}")
    if request.route.total_amt != donation.amount:
        raise ValidationError(f"Donation amount do not match {request.route.total_amt}")
    now = datetime.utcnow()
    await db.donation_paid(donation.id, donation.amount, paid_at=now, fee_msat=request.route.total_fees * 1000, claimed_at=now)
    donation = await db.query_donation(id=donation.id)
    track_donation(donation)
    return donation


@router.post("/donation/{donation_id}/cancel")
async def cancel_donation(donation_id: UUID, db=Depends(get_donations_db), me=Depends(get_donator)):
    """
    It only works for HODL invoices
    """
    donation: Donation = await db.cancel_donation(donation_id)
    if donation.donator.id != me.id:
        # Exception will rollback the transaction
        raise HTTPException(status_code=403, detail="You are not the donator")
    if donation.r_hash is not None:
        await lnd.cancel_invoice(donation.r_hash)


@router.get("/donations/latest", response_model=list[Donation])
async def latest_donations(offset: int = 0, db=Depends(get_donations_db)):
    return await db.query_donations(
        DonationDb.paid_at.isnot(None)
        & DonationDb.cancelled_at.is_(None)
        & (
            (DonationDb.receiver_id != DonationDb.donator_id)
            | DonationDb.receiver_id.is_(None)
        ),
        limit=settings.latest_donations_count, offset=offset,
    )


@router.get("/donations/by-donator/{donator_id}", response_model=list[Donation])
async def donator_donations(donator_id: UUID, db=Depends(get_donations_db), me=Depends(only_me), offset: int = 0):
    return await db.query_donations(
        DonationDb.paid_at.isnot(None) & (
            (DonationDb.donator_id == donator_id)
            | (DonationDb.receiver_id == donator_id)
        ),
        offset=offset,
    )


@router.get("/donations/by-donator/{donator_id}/sent", response_model=list[Donation])
async def donator_donations_sent(donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me), offset: int = 0):
    return await DonationsDbLib(db).query_donations(
        DonationDb.id.in_(select(sent_donations_subquery(donator_id).c.id)), offset=offset,
    )


@router.get("/donations/by-donator/{donator_id}/received", response_model=list[Donation])
async def donator_donations_received(donator_id: UUID, db=Depends(get_db_session), me=Depends(only_me), offset: int = 0):
    return await DonationsDbLib(db).query_donations(
        DonationDb.id.in_(select(received_donations_subquery(donator_id).c.id)), offset=offset,
    )
