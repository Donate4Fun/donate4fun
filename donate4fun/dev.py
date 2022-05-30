from .settings import load_settings
from .db import load_db


async def load():
    with load_settings() as settings:
        async with load_db() as db:
            return settings, db
