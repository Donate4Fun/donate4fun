import asyncio
import secrets
from uuid import uuid4, UUID
from contextvars import ContextVar

import anyio
import pytest

from donate4fun.core import as_task
from donate4fun.types import LightningAddress
from donate4fun.models import OAuthState, WithdrawalToken


async def test_anyio():
    async with anyio.create_task_group() as tg:
        tg.start_soon(task)
        print("before exit")
    print("exited")


async def task():
    async for i in async_gen():
        print("gen", i)
        if i > 2:
            break


async def async_gen():
    async with anyio.create_task_group() as tg:
        tg.start_soon(asyncio.sleep, 100)
        for i in range(100):
            yield i


blah = ContextVar("blah")


@pytest.fixture
async def my_context_var():
    blah.set("hello")
    assert blah.get() == "hello"
    yield blah


async def test_blah(my_context_var):
    assert my_context_var.get() == "hello"


ctx_var = ContextVar('my-var', default=0)


@as_task
async def some_task(out_ev, in_ev):
    assert ctx_var.get() == 2
    ctx_var.set(3)
    out_ev.set()
    await in_ev.wait()
    assert ctx_var.get() == 3


@pytest.fixture
async def async_fixture():
    ctx_var.set(1)
    yield
    assert ctx_var.get() == 2


async def test_context_leak(async_fixture):
    """
    Test that as_task creates copy of parent context and don't leak context vars
    """
    assert ctx_var.get() == 1
    ctx_var.set(2)
    in_ev = asyncio.Event()
    out_ev = asyncio.Event()
    async with some_task(in_ev, out_ev):
        assert ctx_var.get() == 2
        await in_ev.wait()
        assert ctx_var.get() == 2
        out_ev.set()


@pytest.mark.parametrize('text', ['⚡ BitFrankie@zbd.gg'])
async def test_parse_lightning_address(text: str):
    assert LightningAddress.parse(text) != None  # noqa


async def test_jws(settings):
    orig = WithdrawalToken(withdrawal_id=uuid4())
    new = WithdrawalToken.from_jwt(orig.to_jwt())
    assert new == orig


async def test_jwe(settings):
    orig_state = OAuthState(
        last_url='http://some-url.com/some-long-path-that-could-be-here',
        donator_id=uuid4(), code_verifier=secrets.token_urlsafe(43),
    )
    token: str = orig_state.to_jwe()
    new_state = OAuthState.from_jwe(token)
    assert new_state == orig_state


async def test_encrypted_jwt(settings):
    orig_state = OAuthState(
        last_url='http://localhost:5173/donator/f28b5bc4-1946-45f7-a7dd-33c0ae002465',
        donator_id=uuid4(), code_verifier=secrets.token_urlsafe(32),
    )
    token: str = orig_state.to_encrypted_jwt()
    assert len(token) <= 500, "Twitter requires state be smaller than 500 symbols"
    new_state = OAuthState.from_encrypted_jwt(token)
    assert new_state == orig_state


async def test_jwt_is_immutable(settings):
    state = OAuthState(last_url='http://a.com', donator_id=UUID(int=0), code_verifier=b'\x00' * 43)
    assert state.to_jwt() == state.to_jwt()


async def test_encrypted_jwt_is_immutable(settings, monkeypatch):
    monkeypatch.setattr('secrets.token_bytes', lambda size: b'\x00' * size)
    state = OAuthState(last_url='http://a.com', donator_id=UUID(int=0), code_verifier=b'\x00' * 43)
    assert state.to_encrypted_jwt() == state.to_encrypted_jwt()


async def test_jwe_is_immutable(settings, monkeypatch):
    monkeypatch.setattr('secrets.token_bytes', lambda size: b'\x00' * size)
    state = OAuthState(last_url='http://a.com', donator_id=UUID(int=0), code_verifier=b'\x00' * 43)
    assert state.to_jwe() == state.to_jwe()
