import logging
import hashlib
from uuid import UUID
from datetime import datetime

from fastapi import Request, Depends, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from furl import furl
from sqlalchemy import select

from .models import (
    Donation, Donator, Invoice, DonateResponse, DonateRequest, DonationPaidRequest, RequestHash
)
from .types import ValidationError
from .social import SocialProviderId, SocialProvider
from .api_utils import (
    get_donator, get_db_session, load_donator, track_donation, get_donations_db, only_me,
)
from .db_libs import GithubDbLib, TwitterDbLib, YoutubeDbLib, DonationsDbLib
from .db_donations import sent_donations_subquery, received_donations_subquery
from .db_models import DonationDb
from .db_social import SocialDbWrapper
from .lnd import lnd
from .settings import settings
from .donation import donate, make_memo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/donate", response_model=DonateResponse)
async def donate_api(
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
        receiver: Donator = await load_donator(db_session, request.receiver_id)
        if not receiver.connected:
            raise ValidationError("Money receiver should have a connected wallet")
        donation.receiver = receiver
    elif request.social_account_id and request.social_provider:
        provider: SocialProvider = SocialProvider.create(request.social_provider)
        social_db: SocialDbWrapper = provider.wrap_db(db_session)
        social_account = await social_db.query_account(id=request.social_account_id)
        setattr(donation, social_db.donation_field, social_account)
        donation.lightning_address = donation.lightning_address or social_account.lightning_address
    elif request.target:
        target = furl(request.target)
        social_provider = SocialProvider.from_url(target)
        await social_provider.apply_target(donation, target, db_session)
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
        twitter_provider = SocialProvider.create(SocialProviderId.twitter.value)
        donation.donator_twitter_account = await twitter_provider.query_or_fetch_account(
            twitter_provider.wrap_db(db_session), handle=request.donator_twitter_handle
        )
    pay_req, donation = await donate(donation, db_session)
    if pay_req is None:
        # FIXME: balance is saved in cookie to notify extension about balance change, but it should be done via VAPID
        web_request.session['balance'] = (await db_session.query_donator(id=donator.id)).balance
    return DonateResponse(donation=donation, payment_request=pay_req)


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


@router.get("/donation/{donation_id}/invoice")
async def get_invoice(donation_id: UUID, db_session=Depends(get_donations_db)):
    donation: Donation = await db_session.query_donation(id=donation_id)
    if donation.paid_at is None:
        invoice: Invoice = await lnd.lookup_invoice(donation.r_hash)
        if invoice is None or invoice.state == 'CANCELED':
            logger.debug(f"Invoice {invoice} cancelled, recreating")
            invoice = await lnd.create_invoice(memo=make_memo(donation), value=donation.amount)
            await db_session.update_donation(donation_id=donation_id, r_hash=invoice.r_hash)
        return RedirectResponse(f'lightning:{invoice.payment_request}', status_code=307)
    else:
        return RedirectResponse(f'/donation/{donation.id}', status_code=303)


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
