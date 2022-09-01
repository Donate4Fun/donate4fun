import yaml
import os
import logging
from typing import Any
from contextvars import ContextVar
from contextlib import asynccontextmanager, contextmanager

from pydantic import BaseSettings, BaseModel, Field, AnyUrl

Url = str
logger = logging.getLogger(__name__)


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_base_url: AnyUrl


class YoutubeSettings(BaseModel):
    oauth: OAuthSettings
    service_account_key_file: str
    api_key: str


class DbSettings(BaseModel):
    url: str
    echo: bool = False
    isolation_level: str = 'READ COMMITTED'
    connect_args: dict[str, Any] = {}
    pool_size: int = 10
    max_overflow: int = 20


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


class LndSettings(BaseModel):
    url: Url
    lnurl_base_url: AnyUrl
    macaroon_by_network: str | None = None
    macaroon_by_path: str | None = None
    invoice_expiry: int = 3600  # In seconds
    private: bool = True


class FastApiSettings(BaseModel):
    debug: bool
    root_path: str


class BugsnagSettings(BaseModel):
    api_key: str
    release_stage: str
    app_version: str


class RollbarSettings(BaseModel):
    access_token: str
    environment: str
    code_version: str


def yaml_config_source(settings: BaseSettings) -> dict[str, Any]:
    return yaml.safe_load(open(os.getenv('DONATE4FUN_CONFIG', 'config.yaml')))


class Settings(BaseSettings):
    lnd: LndSettings
    youtube: YoutubeSettings
    db: DbSettings
    log: LoggingConfig
    fastapi: FastApiSettings
    bugsnag: BugsnagSettings | None
    rollbar: RollbarSettings | None
    hypercorn: dict[str, Any]
    jwt_secret: str
    min_withdraw: int  # Limit in sats for claiming
    donator_name_seed: int
    fee_limit: int
    withdraw_timeout: int
    ownership_message: str
    cookie_domain: str | None = None

    class Config:
        env_nested_delimiter = '__'

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


class ContextualObject:
    def __init__(self, name: str):
        self.__dict__['var'] = ContextVar(name)

    @contextmanager
    def assign(self, var):
        token = self.__dict__['var'].set(var)
        try:
            yield self
        finally:
            self.var.reset(token)

    def __getattr__(self, attrname):
        return getattr(self.__dict__['var'].get(), attrname)

    def __setattr__(self, attrname, value):
        return setattr(self.__dict__['var'].get(), attrname, value)


settings = ContextualObject("settings")


@asynccontextmanager
async def load_settings():
    _settings = Settings()
    with settings.assign(_settings):
        log_config = _settings.log.dict(by_alias=True)
        logging.config.dictConfig(log_config)
        logger.debug('setting loaded: %s', _settings.json())
        yield _settings
