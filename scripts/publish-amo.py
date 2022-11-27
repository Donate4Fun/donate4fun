#!/bin/env python

import jwt
import requests
import uuid
import os
import time
from subprocess import check_output


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
        upload = session.post(
            prefix + 'addons/upload/',
            data=dict(channel='listed'),
            files=dict(upload=open('extensions/firefox.zip', 'rb'))
        ).json()
        while not upload['processed']:
            print("upload", upload)
            time.sleep(1)
            upload = session.get(upload['url']).json()
        if not upload['valid']:
            raise Exception(f"upload invalid: {upload}")
        release_notes = check_output('npx conventional-changelog --commit-path=. -r 2', cwd='extensions/src', shell=True, text=True)
        session.post(
            prefix + 'addons/addon/donate4fun/versions/',
            data=dict(upload=upload['uuid']),
            files=dict(source=check_output('./scripts/download-tar-for-amo.sh')),
        )
        session.post(prefix + 'addons/addon/donate4fun/versions/', json=dict(
            approval_notes=open('docs/instruction-for-amo.md').read(),
            compatibility=['firefox'],
            release_notes={'en-US': release_notes},
            upload=upload['uuid'],
        ))


if __name__ == '__main__':
    try:
        main()
    except requests.HTTPError as exc:
        print('HTTPError', exc, exc.response.text)
        raise
