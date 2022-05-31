from __future__ import annotations
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime

import jwt
from dataclasses_json import dataclass_json
from pydantic import BaseModel, validator
from funkybob import UniqueRandomNameGenerator
from multiavatar.multiavatar import multiavatar

from .settings import settings
from .core import to_datauri
from .types import Url


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
    r_hash: str
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
