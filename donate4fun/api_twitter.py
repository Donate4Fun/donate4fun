from uuid import UUID

import posthog
from fastapi import Depends, APIRouter, HTTPException

from .models import TwitterAccount, TransferResponse, Donator, TwitterAccountOwned, Donation
from .types import ValidationError
from .api_utils import get_donator, load_donator, get_db_session
from .twitter import make_prove_message
from .db_models import DonationDb

router = APIRouter(prefix='/twitter')


@router.get("/account/{account_id}", response_model=TwitterAccountOwned)
async def twitter_account(account_id: UUID, db=Depends(get_db_session), me=Depends(get_donator)):
    return await db.query_twitter_account(id=account_id, owner_id=me.id)


@router.get("/linked", response_model=list[TwitterAccount])
async def my_linked_twitter_accounts(db=Depends(get_db_session), me=Depends(get_donator)):
    return await db.query_donator_twitter_accounts(me.id)


@router.get("/ownership-message")
async def twitter_ownership_message(me=Depends(get_donator)):
    return dict(message=make_prove_message(me.id))


@router.post('/account/{account_id}/transfer', response_model=TransferResponse)
async def twitter_account_transfer(account_id: UUID, db=Depends(get_db_session), donator: Donator = Depends(get_donator)):
    donator = await load_donator(db, donator.id)
    account: TwitterAccountOwned = await db.query_twitter_account(id=account_id, owner_id=donator.id)
    if not account.owner == donator:
        raise HTTPException(status_code=401, detail="You should prove that you own Twitter accoutn")
    if not donator.connected:
        raise ValidationError("You should have a connected auth method to claim donations")
    if account.balance != 0:
        amount = await db.transfer_twitter_donations(twitter_account=account, donator=donator)
    posthog.capture(donator.id, 'transfer', dict(source='twitter', amount=amount))
    return TransferResponse(amount=amount)


@router.get("/account/{account_id}/donations/by-donatee", response_model=list[Donation])
async def donatee_donations(account_id: UUID, db=Depends(get_db_session)):
    return await db.query_donations((DonationDb.twitter_account_id == account_id) & DonationDb.paid_at.isnot(None))
