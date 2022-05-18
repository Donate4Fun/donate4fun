from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, ParseResult


def query(url, **params):
    parsed = urlparse(url)
    return urlunparse(ParseResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=parsed.path,
        params=parsed.params,
        fragment=parsed.fragment,
        query=urlencode(parse_qsl(parsed.query) + list(params.items())),
    ))
