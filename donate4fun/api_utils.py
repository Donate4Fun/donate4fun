import re
import unicodedata
from uuid import uuid4, UUID

from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm.exc import NoResultFound  # noqa - imported from other modules

from .models import Donator, Credentials
from .db import DbSession, db
from .core import ContextualObject
from .types import LightningAddress


task_group = ContextualObject('task_group')


def get_donator(request: Request):
    creds = Credentials(**request.session)
    if creds.donator is not None:
        donator = Donator(id=creds.donator)
    else:
        donator = Donator(id=uuid4())
        creds.donator = donator.id
    request.session.update(**creds.to_json_dict())
    return donator


def only_me(request: Request, donator_id: UUID, me=Depends(get_donator)):
    if donator_id != me.id:
        raise HTTPException(status_code=403, detail="This API available only to the owner")
    return me


async def load_donator(db: DbSession, donator_id: UUID) -> Donator:
    try:
        return await db.query_donator(id=donator_id)
    except NoResultFound:
        return Donator(id=donator_id)


async def get_db_session():
    async with db.session() as session:
        yield session


def scrape_lightning_address(text: str):
    # Remove Mark characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'M')
    if match := re.search(fr'⚡\W*({LightningAddress.regexp[1:-1]})', text):
        return match.group(1)
