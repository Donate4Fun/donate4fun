import * as jose from "jose";

export async function decodeJwt(token) {
  const jwks = jose.createRemoteJWKSet(new URL(`${window.location.origin}/.well-known/jwks.json`));
  const { payload } = await jose.jwtVerify(token, jwks);
  return payload;
}

