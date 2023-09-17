from datetime import datetime
from typing import Any

from pydantic import BaseModel, AnyUrl

from .types import ValidationError


class APIError(Exception):
    def __init__(self, message: str, *, status_code: int, body: Any):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __str__(self) -> str:
        return f"{self.args[0]}: {self.body} [{self.status_code}]"


MediaID = int
TwitterHandle = str


class UnsupportedTwitterUrl(ValidationError):
    pass


class InvalidResponse(Exception):
    pass


TweetId = int
AuthorId = int
ConversationId = int
TwitterHandle = str
MediaKey = str
OAuth1Token = dict


class TweetReference(BaseModel):
    id: TweetId
    type: str  # replied_to | ...


class BaseEntity(BaseModel):
    start: int
    end: int


class MentionEntity(BaseEntity):
    id: TweetId
    username: TwitterHandle


class UrlEntity(BaseEntity):
    display_url: str  # It actually lacks a scheme
    url: AnyUrl
    expanded_url: AnyUrl
    media_key: MediaKey | None = None


class TweetEntities(BaseModel):
    mentions: list[MentionEntity] = []
    urls: list[UrlEntity] = []


class Tweet(BaseModel):
    id: TweetId
    text: str
    conversation_id: ConversationId | None = None
    author_id: AuthorId | None = None
    created_at: datetime | None = None
    in_reply_to_user_id: AuthorId | None = None
    referenced_tweets: list[TweetReference] = []
    edit_history_tweet_ids: list[TweetId] = []
    entities: TweetEntities | None = None

    @property
    def replied_to(self) -> TweetId:
        return next((ref.id for ref in self.referenced_tweets if ref.type == 'replied_to'), None)
