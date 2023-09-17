import logging
import time
import json
import sys
import webbrowser
from contextvars import ContextVar
from contextlib import asynccontextmanager
from uuid import UUID
from functools import cache
from hashlib import md5
from urllib.parse import parse_qs, urlencode
from io import BytesIO

import anyio
import pytest
import yaml
from asgi_testclient import TestClient
from authlib.jose import jwt
from PIL import Image, ImageChops
from vcr.filters import replace_query_parameters
from furl import furl
from vcr.request import Request as VcrRequest
from vcr.errors import CannotOverwriteExistingCassetteException

from donate4fun.models import Donator, Credentials
from donate4fun.social import SocialProvider
from donate4fun.db import Notification
from donate4fun.settings import Settings, settings
from donate4fun.core import to_base64
from donate4fun.api_utils import decode_jwt
from donate4fun.dev_helpers import get_carol_lnd, get_alice_lnd

logger = logging.getLogger(__name__)
# This file is needed because pytest modifies "assert" only in test_*.py files


def pytest_assert(left, right, message):
    assert left == right, message


def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data"""
    if data.count('\n') > 0:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)  # to use with safe_dump


def fixture_filename(name: str) -> str:
    return f'tests/autofixtures/{name}.yaml'


def load_fixture(name: str) -> dict:
    with open(fixture_filename(name)) as f:
        return yaml.unsafe_load(f)


def save_fixture(name: str, data: dict):
    with open(fixture_filename(name), 'w') as f:
        yaml.dump(data, f)


def verify_fixture(data: dict, name: str):
    filename = f'tests/autofixtures/{name}.yaml'
    try:
        original = load_fixture(name)
        assert data == original, f"Response for {filename} differs"
    except FileNotFoundError:
        save_fixture(name, data)


def verify_image_fixture(data: dict, image: Image, name: str):
    # Compare only digest to make fixtures smaller and avoid nasty pytest bug
    # https://github.com/pytest-dev/pytest/issues/8998
    filename = f'tests/autofixtures/{name}.yaml'
    image_filename = f'tests/autofixtures/{name}.png'
    try:
        with open(filename) as f:
            original = yaml.unsafe_load(f)
        original_image = Image.open(image_filename)
        diff_image = concat_images(original_image, image)
        buff = BytesIO()
        diff_image.save(buff, format="PNG")
        diff_image_url = f"data:image/png;base64,{to_base64(buff.getvalue())}"
        assert original == data, f"Response for {filename} differs, difference {diff_image_url}"
    except FileNotFoundError:
        with open(filename, 'w') as f:
            yaml.dump(data, f)
        image.save(image_filename)


def concat_images(image_a: Image, image_b: Image):
    result = Image.new('RGBA', (image_a.width, image_a.height + image_b.height + max(image_a.height, image_b.height)))
    result.paste(image_a, (0, 0))
    result.paste(image_b, (0, image_a.height))
    diff_image = ImageChops.difference(image_a, image_b)
    result.paste(diff_image, (0, image_a.height + image_b.height))
    return result


var = ContextVar('var')


@pytest.fixture
async def fixture_test():
    token = var.set('asd')
    yield
    var.reset(token)


async def test_async_context(fixture_test):
    assert var.get() == 'asd'


def check_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, f"{response.url} responded with {response.text}"
    return response


def verify_response(response, name, status_code=None):
    if status_code is not None:
        check_response(response, status_code)
    content_type = response.headers['content-type']
    if 300 <= response.status_code < 400:
        data = dict(status_code=response.status_code, location=response.headers['location'])
    elif content_type == 'application/json':
        data = dict(status_code=response.status_code, json=response.json())
    elif content_type == 'application/xml':
        data = dict(status_code=response.status_code, xml=response.text)
    elif content_type.startswith('text/html'):
        data = dict(status_code=response.status_code, html=response.text)
    elif content_type == 'image/png':
        # Compare only digest to make fixtures smaller and avoid nasty pytest bug
        # https://github.com/pytest-dev/pytest/issues/8998
        image = Image.open(BytesIO(response.content))
        scaled_image = image.resize((image.width // 2, image.height // 2))
        data = dict(status_code=response.status_code, md5=md5(response.content).digest())
        verify_image_fixture(data, scaled_image, name)
        return
    else:
        raise ValueError(f"Not implemented for {content_type}")
    verify_fixture(data, name)


freeze_time = pytest.mark.freeze_time('2022-02-02 22:22:22', ignore=['logging'])


@asynccontextmanager
async def check_notification(client: TestClient, topic: str, id_: UUID | None = None):
    if id_ is not None:
        topic = f'{topic}:{id_}'
    logger.trace(f"Subscribing to {topic}")
    # WORKAROUND: we use asgi_testclient.TestClient because fastapi.TestClient doesn't support websockets
    async with client.ws_session(f"/api/v1/subscribe/{topic}", client) as ws:
        logger.trace(f"Subscribed to {topic}")
        yield
        with anyio.fail_after(5):
            notification = Notification.parse_obj(await ws.receive_json())
            logger.trace(f"Received notification from {topic}: {notification}")
        assert notification.status == 'OK'


def login_to(client, settings: Settings, donator: Donator):
    # Relogin to rich donator (with balance > 0)
    creds = Credentials(
        donator=donator.id,
        lnauth_pubkey=donator.lnauth_pubkey,
    )
    token: str = jwt.encode(
        dict(alg='HS256'),
        dict(
            exp=int(time.time()) + 10 ** 6,
            **creds.to_json_dict(),
        ),
        settings.jwt_secret,
    ).decode()
    client.cookies = dict(session=token)


def is_json(headers: dict[str, list[str]]) -> bool:
    content_types = {key.lower(): value for key, value in headers.items()}.get('content-type', [])
    if isinstance(content_types, str):
        content_types = [content_types]
    return any(content_type.startswith('application/json') for content_type in content_types)


def enabler(var):
    @asynccontextmanager
    async def enable():
        """
        This function should be async for context var to work
        because pytest uses different contexts for sync/async functions
        """
        token = var.set(True)
        try:
            yield
        finally:
            var.reset(token)
    return enable


disable_vcr_var = ContextVar("disable-vcr", default=False)
disable_vcr = enabler(disable_vcr_var)
lnd_vcr_enabled = ContextVar('enable-lnd-vcr', default=False)
enable_lnd_vcr = enabler(lnd_vcr_enabled)


@cache
def lnd_origins() -> list[str]:
    return [lnd.settings.url for lnd in [get_alice_lnd(), get_carol_lnd()]]


SECRET_OAUTH_PARAMS = ['oauth_token_secret']


def sanitize_request(request: VcrRequest):
    if disable_vcr_var.get():
        return None
    if 'grpc-metadata-macaroon' in request.headers:
        request.headers['grpc-metadata-macaroon'] = 'secret'
    if 'authorization' in request.headers:
        request.headers['authorization'] = 'secret'

    if is_json(request.headers):
        body = json.loads(request.body)
        if 'client_secret' in body:
            body['client_secret'] = 'secret'
            request.body = json.dumps(body)
    if request.host == 'youtube.googleapis.com':
        # WORKAROUND: key is a private credential
        replace_query_parameters(request, [('key', None)])
    if request.host == 'test':
        # Ignore testclient requests
        return None
    if not lnd_vcr_enabled.get() and furl(request.url).origin in lnd_origins():
        # Ignore requests to lnd
        return None
    if request.query:
        request.uri = furl(
            url=request.uri,
            query=[(key, 'secret' if key in SECRET_OAUTH_PARAMS else value) for key, value in request.query],
        ).url
    return request


def sanitize_response(response):
    # WORKAROUND: this is a fix for vcrpy async handler
    if 'url' in response:
        response['url'] = ''
    if is_json(response.get('headers', {})) and response.get('content'):
        try:
            body = json.loads(response['content'])
        except json.decoder.JSONDecodeError:
            pass
        else:
            if 'access_token' in body:
                body['access_token'] = 'secret'
            if 'refresh_token' in body:
                body['refresh_token'] = 'secret'
            response['content'] = json.dumps(body)
    else:
        query = parse_qs(response.get('content', ''))
        if query:
            for param in SECRET_OAUTH_PARAMS:
                if param in query:
                    query[param] = ['secret']
            response['content'] = urlencode(query, doseq=True)
    return response


def mark_vcr(func):
    markers = [
        pytest.mark.block_network(allowed_hosts=['localhost', '::1', '127.0.0.1']),
        pytest.mark.vcr(
            before_record_request=sanitize_request,
            before_record_response=sanitize_response,
            sequential=True,
            custom_patches=((sys.modules['tests.test_util'], 'InputAsker', InputAskerPatched),),
        ),
    ]
    for marker in markers:
        func = marker(func)
    return func


async def ask_user_browser(name: str, url: str, prompt: str) -> str:
    response = await InputAsker().ask(name, url, prompt)
    return response['headers']['location']


class InputAsker:
    async def ask(self, name: str, url: str, prompt: str) -> dict:
        """
        name is a unique name to identify this input in cassette
        """
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            prompt += '\n' + url
        # TODO: use local webserver to automatize process more
        # TODO: user async input here
        response_url = input(prompt + '\n')
        return dict(
            status_code=307,
            headers=dict(location=response_url),
        )


class InputAskerPatched(InputAsker):
    cassette = None  # This will be set by pyvcr

    async def ask(self, name: str, url: str, prompt: str):
        vcr_request = VcrRequest(method='GET', uri=url, headers=dict(
            name=name,
            prompt=prompt,
        ), body=b'')
        if self.cassette.can_play_response_for(vcr_request):
            return self.cassette.play_response(vcr_request)
        if self.cassette.write_protected and self.cassette.filter_request(vcr_request):
            raise CannotOverwriteExistingCassetteException(cassette=self.cassette, failed_request=vcr_request)
        track = self.cassette.forward()
        response: dict = await super().ask(name, url, prompt)
        self.cassette.record(track, vcr_request, response)
        return response


async def follow_oauth_flow(client, provider: SocialProvider, name: str, return_to: str, **params):
    response = check_response(await client.get(
        f'/api/v1/{provider.value}/oauth',
        params=dict(return_to=return_to, **params),
        headers=dict(referer=settings.base_url),
    )).json()
    auth_url: str = response['url']
    encrypted_state: str = furl(auth_url).query.params['state']
    redirect_url: str = await ask_user_browser(
        name,
        url=auth_url,
        prompt="Open this url, authorize and paste url after redirect here:",
    )
    code: str = furl(redirect_url).query.params['code']
    response = await client.get(
        f'/api/v1/oauth-redirect/{provider.value}',
        params=dict(state=encrypted_state, code=code),
    )
    verify_oauth_redirect(response, return_to, name)


def verify_oauth_redirect(response, return_to: str, name: str):
    check_response(response, 307)
    redirect_url = furl(response.headers['location'])
    assert redirect_url.path == return_to
    # WORKAROUND: we can't put full JWT to fixture because it changes every time because
    # ECDSA signature always uses PRNG (/dev/urandom in case of cryptography package)
    # and it's quite compilcated to replace it with predictable PRNG
    assert list(redirect_url.query.params) == ['toasts']
    toasts: dict = decode_jwt(redirect_url.query.params['toasts'])
    verify_fixture(toasts, f'oauth-redirect-toasts-{name}')
