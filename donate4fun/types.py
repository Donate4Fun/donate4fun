import re
from binascii import b2a_hex
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from lnpayencode import lndecode, LnAddr


Url = str


class LightningAddress(str):
    # https://github.com/lnurl/luds/blob/luds/16.md
    domain_regexp = r'(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})\.[a-z]{2,}'  # noqa
    # for local development
    #domain_regexp = r'(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})(\.[a-z]{2,})?(:\d{1,5})?'  # noqa
    regexp = r'^[a-z0-9-_.]+@' + domain_regexp + '$'

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not re.match(cls.regexp, v):
            raise ValidationError
        return str(v)


class PaymentRequest(str):
    prefixes = ('lnbc', 'lntb', 'lntbs', 'lnbcrt')

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, data: str):
        if data.startswith(cls.prefixes):
            return cls(data)
        else:
            raise ValueError(f"valid payment request should start with one of {cls.prefixes}")

    def decode(self) -> LnAddr:
        return lndecode(self)


class RequestHash(str):
    def __init__(self, data: bytes):
        self.data = data

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, data: str):
        if isinstance(data, cls):
            return data
        elif isinstance(data, str):
            if re.match(r'[0-9a-f]{64}', data):
                return cls(bytes.fromhex(data))
            else:
                return cls(urlsafe_b64decode(data))
        else:
            raise ValueError("Argument should be of type {cls} or str, not {type(data)}")

    @property
    def as_hex(self):
        return b2a_hex(self.data).decode()

    @property
    def as_base64(self):
        return urlsafe_b64encode(self.data).decode()

    def to_json(self):
        return self.as_base64

    def __repr__(self):
        return f'{type(self).__name__}({self.as_base64})'

    def __eq__(self, other):
        return isinstance(other, RequestHash) and self.data == other.data


class ValidationError(Exception):
    pass


class UnsupportedTarget(ValidationError):
    pass


class NotEnoughBalance(ValidationError):
    pass


class NotFound(Exception):
    pass


class InvalidDbState(Exception):
    pass


class EntityTooOld(Exception):
    pass
