import yaml
import os
import logging
from typing import Any
from contextvars import ContextVar
from contextlib import contextmanager

from pydantic import BaseSettings, BaseModel, Field

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


class FormatterConfig(BaseModel):
    format: str
    datefmt: str = None
    style: str = '%'
    validate_: str = Field(None, alias='validate')


class FilterConfig(BaseModel):
    name: str


class HandlerConfig(BaseModel):
    class_: str = Field(None, alias='class')
    level: str = None
    formatter: str = None
    filters: list[str] = []
    stream: str = None


class LoggerConfig(BaseModel):
    level: str
    propagate: bool = True
    filters: list[str] = []
    handlers: list[str] = []


class LoggingConfig(BaseModel):
    version: int
    formatters: dict[str, FormatterConfig] = {}
    filters: dict[str, FilterConfig] = {}
    handlers: dict[str, HandlerConfig] = {}
    loggers: dict[str, LoggerConfig] = {}
    root: LoggerConfig
    disable_existing_loggers: bool
    incremental: bool = False


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
    log: LoggingConfig

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
    settings = Settings()
    log_config = settings.log.dict(by_alias=True)
    logging.config.dictConfig(log_config)
    token = settings_var.set(settings)
    try:
        yield settings
    finally:
        settings_var.reset(token)


def settings():
    return settings_var.get()
