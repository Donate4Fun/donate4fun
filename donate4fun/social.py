from abc import ABC, abstractmethod

from furl import furl

from .db import DbSession
from .db_social import SocialDbWrapper
from .models import SocialProviderId, SocialProviderSlug, Donation, SocialAccount
from .types import UnsupportedTarget


class SocialProvider(ABC):
    @abstractmethod
    async def query_or_fetch_account(self, db: DbSession, handle: str):
        pass

    @abstractmethod
    def wrap_db(self, db_session: DbSession) -> SocialDbWrapper:
        pass

    @abstractmethod
    async def apply_target(self, donation: Donation, target: str, db_session: DbSession):
        """
        Resolves target url and fills donation fields
        """
        pass

    @abstractmethod
    def get_account_path(self, account: SocialAccount) -> str:
        pass

    @abstractmethod
    def set_donation_receiver(self, donation: Donation, receiver: SocialAccount):
        pass

    @staticmethod
    def create(provider: SocialProviderId) -> 'SocialProvider':
        match provider:
            case SocialProviderId.twitter:
                from .twitter_provider import TwitterProvider
                return TwitterProvider()
            case SocialProviderId.youtube:
                from .youtube_provider import YoutubeProvider
                return YoutubeProvider()
            case SocialProviderId.github:
                from .github_provider import GithubProvider
                return GithubProvider()
            case SocialProviderId.donate4fun:
                from .donate4fun_provider import Donate4FunProvider
                return Donate4FunProvider()
            case _:
                raise NotImplementedError

    @classmethod
    def from_url(cls, target: furl):
        match target.host:
            case 'youtube.com' | 'www.youtube.com' | 'youtu.be':
                return cls.create(SocialProviderId.youtube)
            case 'twitter.com' | 'www.twitter.com':
                return cls.create(SocialProviderId.twitter)
            case 'github.com' | 'www.github.com':
                return cls.create(SocialProviderId.github)
            case _:
                raise UnsupportedTarget("URL is invalid")

    @classmethod
    def from_slug(cls, slug: SocialProviderSlug):
        match slug:
            case SocialProviderSlug.twitter:
                return cls.create(SocialProviderId.twitter)
            case SocialProviderSlug.github:
                return cls.create(SocialProviderId.github)
            case SocialProviderSlug.youtube:
                return cls.create(SocialProviderId.youtube)
            case SocialProviderSlug.donate4fun:
                return cls.create(SocialProviderId.donate4fun)
            case _:
                raise UnsupportedTarget("Slug is invalid")
