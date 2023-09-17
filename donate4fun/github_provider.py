from .social import SocialProvider
from .db import DbSession
from .db_github import GithubDbLib
from .models import GithubUser, Donation

from furl import furl


class GithubProvider(SocialProvider):
    @staticmethod
    def wrap_db(db_session: DbSession) -> GithubDbLib:
        return GithubDbLib(db_session)

    async def query_or_fetch_account(self, db: GithubDbLib, **params) -> GithubUser:
        raise NotImplementedError

    def get_account_path(self, account: GithubUser) -> str:
        return f'/github/{account.id}'

    async def apply_target(self, donation: Donation, target: furl, db_session: DbSession):
        parts = target.path.segments
        username = parts[0]
        db = GithubDbLib(db_session)
        self.set_donation_receiver(donation, await self.query_or_fetch_account(db=db, username=username))
        donation.lightning_address = donation.github_user.lightning_address

    def set_donation_receiver(self, donation: Donation, receiver: GithubUser):
        donation.github_user = receiver
