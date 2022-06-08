from .settings import load_settings
from .db import load_db


async def load():
    async with load_settings() as settings, load_db(settings) as db:
        return settings, db
