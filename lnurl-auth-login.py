#!/usr/bin/env python
import requests
from urllib.parse import urlparse, parse_qs, urlunparse
import ecdsa
import sys
from lnurl.helpers import _lnurl_decode


def main(lnurl):
    lnurl_parsed = urlparse(_lnurl_decode(lnurl))
    query = parse_qs(lnurl_parsed.query, strict_parsing=True)
    k1 = query['k1'][0]
    sk = ecdsa.SigningKey.generate(entropy=ecdsa.util.PRNG(b'seed'), curve=ecdsa.SECP256k1)
    signature = sk.sign_digest_deterministic(bytes.fromhex(k1), sigencode=ecdsa.util.sigencode_der)
    callback_url = urlunparse(list(lnurl_parsed)[:3] + [''] * 3)
    callback_response = requests.get(callback_url, params=dict(
        sig=signature.hex(),
        key=sk.verifying_key.to_string().hex(),
        **{k: v[0] for k, v in query.items()},
    ))
    assert callback_response.json()['status'] == 'OK'


if __name__ == '__main__':
    main(sys.argv[1])
