from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException
from .models import TwitterAccount, TransferResponse, Donator, TwitterAccountOwned
from .core import get_db_session
from .types import ValidationError
from .api_utils import get_donator, load_donator
from .twitter import make_prove_message

router = APIRouter(prefix='/twitter')


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
    if not account.is_my:
        raise HTTPException(status_code=401, detail="You should prove that you own Twitter accoutn")
    if donator.lnauth_pubkey is None:
        raise ValidationError("You should have a connected auth method to claim donations")
    if account.balance != 0:
        amount = await db.transfer_twitter_donations(twitter_account=account, donator=donator)
    return TransferResponse(amount=amount)
