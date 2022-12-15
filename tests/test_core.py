import asyncio
from contextvars import ContextVar

import anyio
import pytest

from donate4fun.core import as_task


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
