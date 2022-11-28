import asyncio
from .app import main


def serve():
    asyncio.run(main([]))
