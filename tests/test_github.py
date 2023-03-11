from uuid import UUID
from datetime import datetime
from base64 import urlsafe_b64encode

import pytest

from donate4fun.models import GithubUser, Donator, SocialProviderId
from donate4fun.db_libs import GithubDbLib

from .test_util import mark_vcr, check_response, login_to, verify_response, follow_oauth_flow, freeze_time


@mark_vcr
@freeze_time
@pytest.mark.parametrize('return_to', ['/donator/me'])
async def test_login_via_oauth(client, settings, monkeypatch, db, freeze_uuids, return_to):
    monkeypatch.setattr('secrets.token_urlsafe', lambda size: urlsafe_b64encode(b'\x00' * size))
    monkeypatch.setattr('secrets.token_bytes', lambda size: b'\x00' * size)

    account = GithubUser(
        user_id=123,
        name='title',
        login='handle',
        avatar_url='http://url.com',
        last_fetched_at=datetime.utcnow(),
    )
    async with db.session() as db_session:
        await GithubDbLib(db_session).save_account(account)

    donator = Donator(id=UUID(int=0))
    login_to(client, settings, donator)
    await follow_oauth_flow(
        client, SocialProviderId.github, name='github-login-via-oauth',
        return_to=return_to, expected_account=account.id,
    )
    me = Donator(**check_response(await client.get('/api/v1/me')).json())
    assert me.id == donator.id
    assert me.connected == True  # noqa

    # Try to relogin from other account to the first account
    other_donator = Donator(id=UUID(int=1))
    login_to(client, settings, other_donator)
    await follow_oauth_flow(
        client, SocialProviderId.github, name='github-login-via-oauth-relogin',
        return_to=return_to,
    )
    me = Donator(**check_response(await client.get('/api/v1/me')).json())
    assert me.id == donator.id
    assert me.connected == True  # noqa

    # Test channel API
    verify_response(await client.get(f'/api/v1/social/github/{account.id}'), 'github-account-owned')
