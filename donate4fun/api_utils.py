import unicodedata
import hashlib
import json
from uuid import uuid4, UUID

import posthog
import httpx
from furl import furl
from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm.exc import NoResultFound  # noqa - imported from other modules
from jwcrypto.jwt import JWT
from jwcrypto.jwk import JWK

from .models import Donator, Credentials, Donation, SocialProvider, SocialAccountOwned, SocialAccount, Toast
from .db import DbSession, db
from .db_libs import TwitterDbLib, YoutubeDbLib, GithubDbLib, DonationsDbLib
from .core import ContextualObject
from .types import LightningAddress, Satoshi
from .settings import settings


task_group = ContextualObject('task_group')


def get_donator(request: Request):
    creds = Credentials(**request.session)
    if creds.donator is not None:
        donator = Donator(id=creds.donator, lnauth_pubkey=creds.lnauth_pubkey)
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
        return await db.query_donator(donator_id)
    except NoResultFound:
        return Donator(id=donator_id)


async def get_db_session():
    async with db.session() as session:
        yield session


async def get_donations_db(db_session=Depends(get_db_session)):
    return DonationsDbLib(db_session)


def scrape_lightning_address(text: str):
    # Remove Mark characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'M')
    return LightningAddress.parse(text)


def track_donation(donation: Donation):
    if donation.twitter_account:
        target_type = 'twitter'
    elif donation.youtube_channel:
        target_type = 'youtube'
    elif donation.receiver:
        target_type = 'donate4fun'
    else:
        target_type = 'unknown'
    if donation.lightning_address:
        via = 'lightning-address'
    else:
        via = 'donate4fun'
    if donation.donator:
        posthog.capture(donation.donator.id, 'donation-paid', dict(amount=donation.amount, target_type=target_type, via=via))


def make_absolute_uri(path: str) -> str:
    return str(furl(url=settings.base_url, path=furl(path).path))


async def auto_transfer_donations(db: DbSession, donation: Donation) -> int:
    """
    Returns sats amount transferred
    """
    if donation.youtube_channel:
        social_db = YoutubeDbLib(db)
    elif donation.twitter_account:
        social_db = TwitterDbLib(db)
    elif donation.github_user:
        social_db = GithubDbLib(db)
    else:
        social_db = None

    if social_db:
        account = getattr(donation, social_db.donation_field)
        if not isinstance(account, social_db.owned_model):
            account: SocialAccountOwned = await social_db.query_account(id=account.id)
        if account.owner_id is not None:
            return await social_db.transfer_donations(account, Donator(id=account.owner_id))
    return 0


def encode_jwt(**claims) -> str:
    jwt = JWT(
        header=dict(alg=settings.jwt.alg),
        claims=dict(iss=settings.base_url, aud=settings.base_url, **claims),
    )
    key = JWK(**settings.jwt.jwk)
    jwt.make_signed_token(key)
    return jwt.serialize()


def decode_jwt(token: str) -> dict:
    jwt = JWT(jwt=token, key=JWK(**settings.jwt.jwk))
    return json.loads(jwt.claims)


def make_redirect(path: str, toasts: list[Toast] = []) -> RedirectResponse:
    url = furl(make_absolute_uri(path))
    if toasts:
        url.add(query_params=dict(toasts=encode_jwt(toasts=[toast.dict() for toast in toasts])))
    return RedirectResponse(url.url)


def oauth_success_messages(linked_account: SocialAccount, transferred_amount: Satoshi) -> list[Toast]:
    yield Toast(
        'success', "Social account is linked",
        f"{linked_account.provider.capitalize()} account {linked_account.unique_name} was successefully linked",
    )
    if transferred_amount > 0:
        yield Toast('success', "Funds claimed", f"{transferred_amount} sats are successefully claimed")


def signin_success_message(account: SocialAccount) -> Toast:
    return Toast(
        'success', 'Successful sign-in',
        f"You've successfully signed in using {account.unique_name} {account.provider.capitalize()} account",
    )


async def raise_on_4xx_5xx(response):
    response.raise_for_status()


class HttpClient(httpx.AsyncClient):
    def __init__(self, **kwargs):
        super().__init__(http2=True, event_hooks=dict(response=[raise_on_4xx_5xx]), **kwargs)


def sha256hash(data: str) -> bytes:
    return hashlib.sha256(data.encode()).digest()


def get_social_provider_db(social_provider: SocialProvider):
    return {
        SocialProvider.youtube: YoutubeDbLib,
        SocialProvider.twitter: TwitterDbLib,
        SocialProvider.github: GithubDbLib,
    }[social_provider]
