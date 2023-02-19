from furl import furl

from .social import SocialProvider
from .db import DbSession
from .models import Donator, Donation


class DonatorDbLib:
    def __init__(self, session: DbSession):
        self.session = session

    async def query_account(self, *, id) -> Donator:
        return await self.session.query_donator(id=id)


class Donate4FunProvider(SocialProvider):
    def wrap_db(self, db_session: DbSession):
        return DonatorDbLib(db_session)

    async def apply_target(self, donation: Donation, target: furl, db_session: DbSession):
        raise NotImplementedError

    async def query_or_fetch_account(self, *, db_session: DbSession, **params):
        raise NotImplementedError

    async def get_account_path(self, account: Donator):
        raise NotImplementedError
