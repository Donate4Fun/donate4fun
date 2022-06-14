from __future__ import annotations
from uuid import UUID
from datetime import datetime

import jwt
from pydantic import BaseModel as PydanticBaseModel, validator, HttpUrl
from funkybob import UniqueRandomNameGenerator
from multiavatar.multiavatar import multiavatar

from .settings import settings
from .core import to_datauri
from .types import Url, RequestHash, PaymentRequest


class BaseModel(PydanticBaseModel):
    class Config:
        json_encoders = {
            RequestHash: lambda r: r.to_json(),
        }


class DonationRequest(BaseModel):
    r_hash: RequestHash
    donator: str
    donatee: str
    trigger: str | None
    message: str | None

    def to_jwt(self) -> str:
        return jwt.encode(self.to_dict(), settings.get().jwt_secret, algorithm="HS256")

    @classmethod
    def from_jwt(cls, token: str) -> 'DonationRequest':
        return cls(**jwt.decode(token, settings.get().jwt_secret, algorithms=["HS256"]))


class DonateRequest(BaseModel):
    target: HttpUrl
    amount: int
    message: str | None
    donater: str | None


class Invoice(BaseModel):
    r_hash: RequestHash
    payment_request: PaymentRequest
    value: int
    memo: str | None
    settle_date: datetime | None
    amt_paid_sat: int | None
    state: str | None

    @validator('settle_date', pre=True)
    def settle_date_validate(cls, settle_date):
        return datetime.fromtimestamp(int(settle_date))


class YoutubeChannel(BaseModel):
    id: UUID
    title: str
    channel_id: str
    thumbnail: Url | None

    class Config:
        orm_mode = True


class Donator(BaseModel):
    id: UUID
    name: str | None
    avatar_url: str | None

    @validator('name', always=True)
    def generate_name(cls, v, values):
        if v is not None:
            return v
        else:
            generator = UniqueRandomNameGenerator(3, separator=' ', seed=settings().donator_name_seed)
            return generator[int(values['id']) % len(generator)].title()

    @validator('avatar_url', always=True)
    def generate_avatar(cls, v, values):
        if v is not None:
            return v
        else:
            return to_datauri('image/svg', multiavatar(str(values['id']), None, None).encode())

    class Config:
        orm_mode = True


class Donation(BaseModel):
    id: UUID
    r_hash: RequestHash
    donator_id: UUID
    donator: Donator
    youtube_channel: YoutubeChannel
    amount: int
    created_at: datetime
    trigger: str | None = None
    message: str | None = None
    paid_at: datetime | None = None
    claimed_at: datetime | None = None

    @validator('donator', pre=True)
    def default_donator(cls, v, values):
        return v or Donator(id=values['donator_id'])

    class Config:
        orm_mode = True


class DonateResponse(BaseModel):
    donation: Donation
    payment_request: PaymentRequest | None


class DonationPaidResponse(BaseModel):
    status: str
    donation: Donation
