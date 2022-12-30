#!/usr/bin/env python
import ecdsa
import sys
import logging
import httpx
import asyncio
from urllib.parse import urlparse, parse_qs, urlunparse
from lnurl.helpers import _lnurl_decode

logger = logging.getLogger(__name__)


async def main(lnurl, seed='seed'):
    lnurl_parsed = urlparse(_lnurl_decode(lnurl))
    query = parse_qs(lnurl_parsed.query, strict_parsing=True)
    k1 = query['k1'][0]
    sk = ecdsa.SigningKey.generate(entropy=ecdsa.util.PRNG(seed.encode()), curve=ecdsa.SECP256k1)
    signature = sk.sign_digest_deterministic(bytes.fromhex(k1), sigencode=ecdsa.util.sigencode_der)
    callback_url = urlunparse(list(lnurl_parsed)[:3] + [''] * 3)
    params = dict(
        sig=signature.hex(),
        key=sk.verifying_key.to_string().hex(),
        **{k: v[0] for k, v in query.items()},
    )
    async with httpx.AsyncClient() as client:
        callback_response = await client.get(callback_url, timeout=3, params=params)
    response = callback_response.json()
    if response['status'] != 'OK':
        print(response)
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    asyncio.run(main(*sys.argv[1:]))
