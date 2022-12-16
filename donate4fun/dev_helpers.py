import os

from .lnd import LndClient
from .settings import LndSettings


def get_polar_dir():
    return os.getenv('POLAR_BASE_DIR', 'polar')


def get_polar_macaroon(name: str):
    return os.path.expanduser(f'{get_polar_dir()}/volumes/lnd/{name}/data/chain/bitcoin/regtest/admin.macaroon')


def get_polar_cert(name: str):
    return os.path.expanduser(f'{get_polar_dir()}/volumes/lnd/{name}/tls.cert')


def get_carol_lnd():
    return LndClient(LndSettings(
        url='https://localhost:8083',
        macaroon_by_path=get_polar_macaroon('carol'),
        tls_cert=get_polar_cert('carol'),
        lnurl_base_url='http://test',
    ))


def get_alice_lnd():
    return LndClient(LndSettings(
        url='https://localhost:8081',
        macaroon_by_path=get_polar_macaroon('alice'),
        tls_cert=get_polar_cert('alice'),
        lnurl_base_url='http://test',
    ))
