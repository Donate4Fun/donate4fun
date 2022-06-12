from .settings import load_settings
from .db import Database


async def load():
    """
    This is just a helper for ipython
    """
    async with load_settings() as settings:
        return settings, Database(settings.db)
