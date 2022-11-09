from .settings import load_settings
from .db import Database


def load():
    """
    This is just a helper for ipython
    """
    with load_settings() as settings:
        return settings, Database(settings.db)
