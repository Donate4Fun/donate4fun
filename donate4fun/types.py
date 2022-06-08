

Url = str
RequestHash = str
PaymentRequest = str


class ValidationError(Exception):
    pass


class UnsupportedTarget(ValidationError):
    pass
