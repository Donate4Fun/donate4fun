from binascii import b2a_hex
from base64 import urlsafe_b64decode, urlsafe_b64encode


Url = str


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


class RequestHash(str):
    def __init__(self, data: bytes):
        self.data = data

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, b64data: str):
        if isinstance(b64data, cls):
            return b64data
        elif isinstance(b64data, str):
            return cls(urlsafe_b64decode(b64data))
        else:
            raise ValueError("Argument should be of type {cls} or str, not {type(b64data)}")

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


class NotEnoughBalance(Exception):
    pass


class NotFound(Exception):
    pass
