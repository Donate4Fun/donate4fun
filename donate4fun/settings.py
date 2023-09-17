import yaml
import os
import logging
import logging.config
import socket
from datetime import timedelta
from typing import Any
from contextlib import contextmanager

from pydantic import BaseSettings, BaseModel, Field, AnyUrl

from .core import ContextualObject

Url = str
logger = logging.getLogger(__name__)


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: str


class YoutubeSettings(BaseModel):
    oauth: OAuthSettings
    service_account_key_file: str
    api_key: str
    refresh_timeout: timedelta


class TwitterOAuth(BaseModel):
    client_id: str
    client_secret: str
    consumer_key: str
    consumer_secret: str


class TwitterSettings(BaseModel):
    bearer_token: str
    greeting: str
    enable_bot: bool
    self_id: int
    dm_check_interval: timedelta
    refresh_timeout: timedelta
    oauth: TwitterOAuth


class GithubSettings(BaseModel):
    client_id: str
    client_secret: str


class DbSettings(BaseModel):
    url: str
    echo: bool = False
    isolation_level: str = 'REPEATABLE READ'
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


class LoggerConfig(BaseModel):
    level: str
    propagate: bool = True
    filters: list[str] = []
    handlers: list[str] = []


class LoggingConfig(BaseModel):
    version: int
    formatters: dict[str, FormatterConfig] = {}
    filters: dict[str, FilterConfig] = {}
    handlers: dict[str, Any] = {}
    loggers: dict[str, LoggerConfig] = {}
    root: LoggerConfig
    disable_existing_loggers: bool
    incremental: bool = False


class LndSettings(BaseModel):
    url: Url
    lnurl_base_url: AnyUrl
    macaroon_by_network: str | None = None
    macaroon_by_path: str | None = None
    tls_cert: str | None = None
    invoice_expiry: int = 3600  # In seconds
    private: bool = True


class FastApiSettings(BaseModel):
    debug: bool
    root_path: str


class BugsnagSettings(BaseModel):
    api_key: str | None
    release_stage: str | None
    app_version: str | None


class RollbarSettings(BaseModel):
    access_token: str
    environment: str
    code_version: str


class LnurlpSettings(BaseModel):
    min_sendable_sats: int
    max_sendable_sats: int
    enable_svg_images: bool = False


class PostHogSettings(BaseModel):
    project_api_key: str = 'fake'
    host: str = ''
    debug: bool = False
    disabled: bool = True


class SentrySettings(BaseModel):
    dsn: AnyUrl
    traces_sample_rate: float
    environment: str


class JwtSettings(BaseModel):
    alg: str
    jwk: dict


def default_settings_file():
    return 'config.yaml'


def yaml_config_source(settings: BaseSettings) -> dict[str, Any]:
    with open(os.getenv('DONATE4FUN_CONFIG', default_settings_file())) as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    lnd: LndSettings
    youtube: YoutubeSettings
    twitter: TwitterSettings
    github: GithubSettings
    db: DbSettings
    log: LoggingConfig
    jwt: JwtSettings
    fastapi: FastApiSettings
    bugsnag: BugsnagSettings | None = None
    rollbar: RollbarSettings | None = None
    google_cloud_logging: bool | None = None
    posthog: PostHogSettings = PostHogSettings()
    sentry: SentrySettings | None = None
    lnurlp: LnurlpSettings
    hypercorn: dict[str, Any]
    jwt_secret: str
    min_withdraw: int  # Limit in sats for claiming
    donator_name_seed: int
    fee_limit: int
    withdraw_timeout: int
    ownership_message: str
    release: bool
    base_url: AnyUrl
    frontend_host: str  # Used by internal browser to generate previews (for static images)
    api_port: int  # Used by internal browser to generate previews
    cookie_domain: str | None = None
    cookie_secure: bool = True
    cookie_http_only: bool = False
    cookie_same_site: str = 'None'
    latest_donations_count: int = 50
    server_name: str = ''

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
                env_settings,
                yaml_config_source,
            )


settings = ContextualObject("settings")


@contextmanager
def load_settings():
    _settings = Settings()
    with settings.assign(_settings):
        log_config = _settings.log.dict(by_alias=True)
        logging.config.dictConfig(log_config)
        if settings.lnd.lnurl_base_url.startswith('http://localnetwork:'):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                localaddr = sock.getsockname()[0]
                settings.lnd.lnurl_base_url = settings.lnd.lnurl_base_url.replace('localnetwork', localaddr)
                logger.info('using autodetected address %s for lnd url', settings.lnd.lnurl_base_url)
        yield _settings
