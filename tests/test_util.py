import logging
import time
import json
from contextvars import ContextVar
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Any
from hashlib import md5
from pathlib import Path
from urllib.parse import parse_qs, urlencode
from io import BytesIO

import anyio
import pytest
import yaml
from authlib.jose import jwt
from PIL import Image, ImageChops
from vcr.filters import replace_query_parameters
from furl import furl

from donate4fun.models import Donator, Credentials, SocialProvider
from donate4fun.db import Notification
from donate4fun.settings import Settings, settings
from donate4fun.core import to_base64
from donate4fun.api_utils import make_absolute_uri

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


def verify_fixture(data: dict[str, Any], name: str):
    filename = f'tests/autofixtures/{name}.yaml'
    try:
        with open(filename) as f:
            original = yaml.unsafe_load(f)
        assert data == original, f"Response for {filename} differs"
    except FileNotFoundError:
        with open(filename, 'w') as f:
            yaml.dump(data, f)


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
    if content_type == 'application/json':
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
async def check_notification(client, topic: str, id_: UUID):
    logger.trace(f"Subscribing to {topic}:{id_}")
    async with client.ws_session(f"/api/v1/subscribe/{topic}:{id_}") as ws:
        logger.trace(f"Subscribed to {topic}:{id_}")
        yield
        with anyio.fail_after(5):
            notification = Notification.parse_obj(await ws.receive_json())
            logger.trace(f"Received notification from {topic}:{id_}: {notification}")
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
    content_types = headers.get('content-type', [])
    if isinstance(content_types, str):
        content_types = [content_types]
    return any(content_type.startswith('application/json') for content_type in content_types)


def remove_credentials_and_testclient(request):
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
    if request.host.startswith('localhost'):
        # Ignore requests to lnd
        return None
    return request


def remove_url_and_sanitize(response):
    # WORKAROUND: this is a fix for vcrpy async handler
    if 'url' in response:
        response['url'] = ''
    if is_json(response['headers']):
        body = json.loads(response['content'])
        if 'access_token' in body:
            body['access_token'] = 'secret'
        if 'refresh_token' in body:
            body['refresh_token'] = 'secret'
        response['content'] = json.dumps(body)
    else:
        query = parse_qs(response.get('content', ''))
        if query:
            if 'oauth_token' in query:
                query['oauth_token'] = ['secret']
            if 'oauth_token_secret' in query:
                query['oauth_token_secret'] = ['secret']
            response['content'] = urlencode(query, doseq=True)
    return response


def mark_vcr(func):
    return pytest.mark.vcr(
        before_record_request=remove_credentials_and_testclient,
        before_record_response=remove_url_and_sanitize,
    )(pytest.mark.block_network(allowed_hosts=['localhost', '::1', '127.0.0.1'])(func))


def load_or_ask(path: str, prompt: str) -> str:
    full_path = Path(__file__).parent / 'autofixtures' / path
    if full_path.exists():
        with open(full_path, 'r') as f:
            data = f.read()
    else:
        data = input(prompt + '\n')
        with open(full_path, 'w+') as f:
            f.write(data)
    return data


async def follow_oauth_flow(client, provider: SocialProvider, name: str, return_to: str, **params):
    response = check_response(await client.get(
        f'/api/v1/{provider}/oauth',
        params=dict(return_to=return_to, **params),
        headers=dict(referer=settings.base_url),
    )).json()
    auth_url: str = response['url']
    encrypted_state: str = furl(auth_url).query.params['state']
    code: str = load_or_ask(f'oauth-flow-{name}.code', f"Open this url {auth_url}, authorize and paste code here:")
    response = await client.get(
        f'/api/v1/oauth-redirect/{provider}',
        params=dict(state=encrypted_state, code=code),
    )
    check_response(response, 307)
    assert response.headers['location'] == make_absolute_uri(return_to)
