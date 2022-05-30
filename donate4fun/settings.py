import yaml
import os
from typing import Any
from contextvars import ContextVar
from contextlib import contextmanager

from pydantic import BaseSettings, BaseModel

Url = str


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: str


class YoutubeSettings(BaseModel):
    oauth: OAuthSettings
    service_account_key_file: str
    api_key: str


class HypercornSettings(BaseModel):
    use_reloader: bool = False


class DbSettings(BaseModel):
    dsn: str
    echo: bool = False


def yaml_config_source(settings: BaseSettings) -> dict[str, Any]:
    return yaml.safe_load(open(os.getenv('DONATE4FUN_CONFIG', 'config.yaml')))


class Settings(BaseSettings):
    domain: str = "donate4.fun"
    lnd_url: Url
    youtube: YoutubeSettings
    db: DbSettings
    hypercorn: HypercornSettings
    jwt_secret: str
    claim_limit: int  # Limit in sats for claiming
    debug: bool
    donator_name_seed: int

    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config_source,
                env_settings,
            )


settings_var = ContextVar("settings")


@contextmanager
def load_settings():
    token = settings_var.set(Settings())
    try:
        yield settings_var.get()
    finally:
        settings_var.reset(token)


def settings():
    return settings_var.get()
