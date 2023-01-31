from uuid import UUID

import posthog
from fastapi import APIRouter, Depends, HTTPException

from .models import TransferResponse, Donator, SocialAccountOwned, Donation, SocialProvider
from .types import ValidationError
from .api_utils import get_db_session, load_donator, get_donator, get_donations_db, get_social_provider_db
from .db_models import DonationDb

router = APIRouter(prefix='/social')


@router.post('/{social_provider}/{account_id}/transfer', response_model=TransferResponse)
async def transfer_social_account_donations(
    social_provider: SocialProvider, account_id: UUID, db=Depends(get_db_session), donator: Donator = Depends(get_donator),
):
    donator = await load_donator(db, donator.id)
    social_db = get_social_provider_db(social_provider)(db)
    account: SocialAccountOwned = await social_db.query_account(id=account_id, owner_id=donator.id)
    if account.owner_id != donator.id:
        raise HTTPException(status_code=401, detail="You should prove that you own YouTube channel")
    if not donator.connected:
        raise ValidationError("You should have a connected auth method to claim donations")
    if account.balance != 0:
        amount = await social_db.transfer_donations(account=account, donator=donator)
    posthog.capture(donator.id, 'transfer', dict(amount=amount, source=social_provider))
    return TransferResponse(amount=amount)


@router.get("/{social_provider}/linked", response_model=None)
async def get_linked_social_accounts(
    db=Depends(get_db_session), me=Depends(get_donator), social_db_lib=Depends(get_social_provider_db),
) -> list[SocialAccountOwned]:
    return await social_db_lib(db).query_linked_accounts(owner_id=me.id)


@router.post("/{social_provider}/{account_id}/unlink")
async def unlink_social_account(
    account_id: UUID, db_session=Depends(get_db_session), me: Donator = Depends(get_donator),
    social_db_lib=Depends(get_social_provider_db),
):
    await social_db_lib(db_session).unlink_account(account_id=account_id, owner_id=me.id)
    me = await db_session.query_donator(id=me.id)
    if not me.connected and me.balance > 0:
        raise ValidationError("Unable to unlink last auth method while you have a positive balance")


@router.get("/{social_provider}/{account_id}/donations/by-donatee", response_model=list[Donation])
async def donatee_donations(account_id: UUID, donations_db=Depends(get_donations_db), social_db=Depends(get_social_provider_db)):
    return await donations_db.query_donations(
        (getattr(DonationDb, social_db.donation_column) == account_id) & DonationDb.paid_at.isnot(None)
    )


class SocialAccountResponse(SocialAccountOwned):
    is_my: bool


@router.get("/{social_provider}/{account_id}", response_model=None)
async def get_social_account(
    account_id: UUID, db=Depends(get_db_session), me=Depends(get_donator), social_db=Depends(get_social_provider_db),
) -> SocialAccountResponse:
    account: SocialAccountOwned = await social_db(db).query_account(id=account_id, owner_id=me.id)
    return dict(
        **account.dict(),
        is_my=account.owner_id == me.id,
    )
