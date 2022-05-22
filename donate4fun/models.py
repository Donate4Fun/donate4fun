from uuid import UUID
from dataclasses import dataclass
from datetime import datetime

import jwt
from dataclasses_json import dataclass_json

from .settings import settings

Url = str


@dataclass_json
@dataclass
class DonationRequest:
    r_hash: str
    donator: str
    donatee: str
    trigger: str | None
    message: str | None

    def to_jwt(self) -> str:
        return jwt.encode(self.to_dict(), settings.get().jwt_secret, algorithm="HS256")

    @classmethod
    def from_jwt(cls, token: str) -> 'DonationRequest':
        return cls(**jwt.decode(token, settings.get().jwt_secret, algorithms=["HS256"]))


@dataclass
class Donation:
    id: UUID
    r_hash: str
    donator: str
    donatee: str
    amount: int
    trigger: str | None
    message: str | None
    created_at: datetime
    claimed_at: datetime | None

    @property
    def amount_sat(self):
        return self.amount / 1000
    pass


class ValidationError(Exception):
    pass


class UnsupportedTarget(ValidationError):
    pass
