from fastapi import Depends, APIRouter
from .models import TwitterAuthor
from .core import get_db_session
from .api_utils import get_donator
from .twitter import make_prove_message

router = APIRouter(prefix='/twitter')


@router.get("/linked-accounts", response_model=list[TwitterAuthor])
async def my_linked_twitter_accounts(db=Depends(get_db_session), me=Depends(get_donator)):
    return await db.query_donator_twitter_accounts(me.id)


@router.get("/ownership-message")
async def twitter_ownership_message(me=Depends(get_donator)):
    return dict(message=make_prove_message(me.id))
