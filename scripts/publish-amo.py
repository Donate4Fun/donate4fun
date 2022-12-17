#!/bin/env python

import jwt
import requests
import uuid
import os
import time
import logging
from subprocess import check_output


logger = logging.getLogger('amo-publisher')


def main():
    prefix = 'https://addons.mozilla.org/api/v5/'
    now = int(time.time())
    token = jwt.encode(dict(
        iss=os.getenv('AMO_JWT_ISSUER'),
        jti=uuid.uuid4().hex,
        iat=now,
        exp=now + 300,
    ), key=os.getenv('AMO_JWT_SECRET'))
    with requests.Session() as session:
        session.hooks = dict(
           response=lambda r, *args, **kwargs: r.raise_for_status()
        )
        session.headers['Authorization'] = f'JWT {token}'
        logger.info("Uploading extension")
        upload = session.post(
            prefix + 'addons/upload/',
            data=dict(channel='listed'),
            files=dict(upload=open('extensions/firefox.zip', 'rb'))
        ).json()
        while not upload['processed']:
            logger.debug("upload %s", upload)
            logger.info("Waiting for extension been processed")
            time.sleep(1)
            upload = session.get(upload['url']).json()
        logger.info("Extension has been processed")
        if not upload['valid']:
            raise Exception(f"upload invalid: {upload}")
        logger.info("Creating source code archive")
        source: bytes = check_output('./scripts/create-tar-for-amo.sh')
        logger.info("Uploading source code archive (%.2dMB)", len(source) / 2 ** 20)
        session.post(
            prefix + 'addons/addon/donate4fun/versions/',
            data=dict(upload=upload['uuid']),
            files=dict(source=('source.tar.gz', source)),
        )
        logger.info("Generating release notes")
        release_notes = check_output(
            'npx conventional-changelog --commit-path=. -r 2', cwd='extensions/src', shell=True, text=True,
        )
        logger.info("Creating new version")
        session.post(prefix + 'addons/addon/donate4fun/versions/', json=dict(
            approval_notes=open('docs/instruction-for-amo.md').read(),
            compatibility=['firefox'],
            release_notes={'en-US': release_notes},
            upload=upload['uuid'],
        ))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except requests.HTTPError as exc:
        print('HTTPError', exc, exc.response.text)
        raise
