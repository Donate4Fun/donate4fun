import asyncio
from contextvars import ContextVar

import anyio
import pytest


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
