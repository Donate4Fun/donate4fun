from __future__ import annotations
from uuid import uuid4, UUID
from datetime import datetime
from typing import Any
import json

import jwt
from pydantic import BaseModel as PydanticBaseModel, validator, HttpUrl, Field, root_validator, EmailStr, AnyUrl
from pydantic.datetime_parse import parse_datetime
from funkybob import UniqueRandomNameGenerator
from multiavatar.multiavatar import multiavatar

from .settings import settings
from .core import to_datauri
from .types import Url, RequestHash, PaymentRequest, LightningAddress


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
    lightning_address: LightningAddress | None
    donator_twitter_handle: str | None
    message: str | None


class NaiveDatetime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        return parse_datetime(int(v)).replace(tzinfo=None)


class Invoice(BaseModel):
    """
    This model is replica of lnd's Invoice message
    https://github.com/lightningnetwork/lnd/blob/master/lnrpc/lightning.proto#L3314
    """
    r_hash: RequestHash
    payment_request: PaymentRequest
    value: int | None
    memo: str | None
    settle_date: NaiveDatetime | None
    amt_paid_sat: int | None
    state: str | None


class PayInvoiceResult(BaseModel):
    creation_date: NaiveDatetime
    fee: float
    fee_msat: int
    fee_sat: float
    payment_hash: RequestHash
    payment_preimage: RequestHash
    status: str
    failure_reason: str
    value: float
    value_msat: int
    value_sat: float


class IdModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class YoutubeChannel(IdModel):
    title: str
    channel_id: str
    thumbnail_url: Url | None
    banner_url: Url | None
    handle: str | None
    balance: int = 0
    total_donated: int = 0
    lightning_address: LightningAddress | None
    last_fetched_at: datetime | None

    class Config:
        orm_mode = True


class YoutubeChannelOwned(YoutubeChannel):
    via_oauth: bool
    owner_id: UUID | None


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
    lightning_address: LightningAddress | None
    last_fetched_at: datetime | None

    class Config:
        orm_mode = True


class TwitterAccountOwned(TwitterAccount):
    via_oauth: bool | None
    owner_id: UUID | None


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
    lightning_address: str | None
    connected: bool | None

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

    @property
    def available_balance(self):
        return self.balance - settings.fee_limit

    class Config:
        orm_mode = True


class Donation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    # This field contains only r_hash for local LND server, i.e. for incoming and outgoing payment
    r_hash: RequestHash | None
    # This field is for transient payment, e.g. when donation is done from external wallet to an external lightning address
    transient_r_hash: RequestHash | None
    # Amount in sats
    amount: int
    # Fee amount in msats. Only for outgoing and transient payments
    fee_msat: int | None

    # Sender
    donator_id: UUID | None
    donator: Donator | None

    # Receiver
    receiver: Donator | None
    youtube_channel: YoutubeChannel | None
    youtube_video: YoutubeVideo | None
    twitter_account: TwitterAccount | None
    twitter_tweet: TwitterTweet | None
    donator_twitter_account: TwitterAccount | None
    lightning_address: LightningAddress | None

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


class DonationPaidRouteInfo(BaseModel):
    total_amt: int
    total_fees: int


class DonationPaidRequest(BaseModel):
    preimage: str
    paymentHash: str
    route: DonationPaidRouteInfo


class Donatee(BaseModel):
    title: str
    thumbnail_url: AnyUrl
    total_donated: int
    type: str
    id: UUID
