from __future__ import annotations
from uuid import uuid4, UUID
from datetime import datetime
from typing import Any
import json

import jwt
from pydantic import BaseModel as PydanticBaseModel, validator, HttpUrl, Field, root_validator, EmailStr
from pydantic.datetime_parse import parse_datetime
from funkybob import UniqueRandomNameGenerator
from multiavatar.multiavatar import multiavatar

from .settings import settings
from .core import to_datauri
from .types import Url, RequestHash, PaymentRequest


class BaseModel(PydanticBaseModel):
    class Config:
        json_encoders = {
            RequestHash: lambda r: r.to_json(),
            int: lambda x: x if abs(x) < 2 ** 31 else str(x),
            datetime: lambda d: f'{d.isoformat()}+00:00',
        }

    def to_json_dict(self):
        return json.loads(self.json())

    def to_jwt(self) -> str:
        return jwt.encode(self.to_json_dict(), settings.jwt_secret, algorithm="HS256")

    @classmethod
    def from_jwt(cls, token: str):
        return cls(**jwt.decode(token, settings.jwt_secret, algorithms=["HS256"]))


class WithdrawalToken(BaseModel):
    withdrawal_id: UUID


class DonateRequest(BaseModel):
    amount: int
    receiver_id: UUID | None
    channel_id: UUID | None
    twitter_account_id: UUID | None
    target: HttpUrl | None
    donator_twitter_handle: str | None
    message: str | None


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
        return parse_datetime(int(settle_date)).replace(tzinfo=None)


class IdModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class YoutubeChannel(IdModel):
    title: str
    channel_id: str
    thumbnail_url: Url | None
    banner_url: Url | None
    balance: int = 0
    last_fetched_at: datetime | None

    class Config:
        orm_mode = True


class YoutubeChannelOwned(YoutubeChannel):
    is_my: bool | None = None


class YoutubeVideo(IdModel):
    youtube_channel: YoutubeChannel
    title: str
    video_id: str
    thumbnail_url: Url | None
    total_donated: int = 0
    default_audio_language: str | None

    class Config:
        orm_mode = True


class TwitterAccount(IdModel):
    user_id: int
    handle: str
    balance: int = 0
    total_donated: int = 0
    name: str | None
    profile_image_url: Url | None

    class Config:
        orm_mode = True


class TwitterAccountOwned(TwitterAccount):
    is_my: bool | None = None


class TwitterTweet(IdModel):
    tweet_id: int

    class Config:
        orm_mode = True


class Donator(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str | None
    avatar_url: str | None
    lnauth_pubkey: str | None
    balance: int = Field(default=0)

    @validator('name', always=True)
    def generate_name(cls, v, values):
        if v is not None:
            return v
        else:
            generator = UniqueRandomNameGenerator(3, separator=' ', seed=settings.donator_name_seed)
            return generator[int(values['id']) % len(generator)].title()

    @validator('avatar_url', always=True)
    def generate_avatar(cls, v, values):
        if v is not None:
            return v
        else:
            return to_datauri('image/svg+xml', multiavatar(str(values['id']), None, None).encode())

    class Config:
        orm_mode = True


class Donation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    r_hash: RequestHash | None
    donator_id: UUID
    donator: Donator
    receiver: Donator | None
    amount: int
    youtube_channel: YoutubeChannel | None
    youtube_video: YoutubeVideo | None
    twitter_account: TwitterAccount | None
    twitter_tweet: TwitterTweet | None
    donator_twitter_account: TwitterAccount | None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: str | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    claimed_at: datetime | None = None

    @root_validator(pre=True)
    def default_donator(cls, values: dict[str, Any]):
        new_values = dict(values)
        if (
            values.get('donator') and values.get('donator_id')
            and (getattr(values['donator'], 'id', None) or values['donator']['id']) != values['donator_id']
        ):
            raise ValueError("donator_id and donator.id should be the same")
        elif donator := values.get('donator'):
            new_values['donator_id'] = getattr(donator, 'id', None) or donator['id']
        elif donator_id := values.get('donator_id'):
            new_values['donator'] = Donator(id=donator_id)
        else:
            raise ValueError("one of donator_id or donator is required")
        return new_values

    class Config:
        orm_mode = True


class DonateResponse(BaseModel):
    donation: Donation
    payment_request: PaymentRequest | None


class Notification(BaseModel):
    id: UUID | str
    status: str
    message: str | None


class YoutubeNotification(Notification):
    vid: str
    total_donated: int


class Credentials(BaseModel):
    donator: UUID | None
    lnauth_pubkey: str | None


class SubscribeEmailRequest(BaseModel):
    email: EmailStr


class TransferResponse(BaseModel):
    amount: int


class DonatorStats(BaseModel):
    total_donated: int
    total_claimed: int
    total_received: int

    class Config:
        orm_mode = True
