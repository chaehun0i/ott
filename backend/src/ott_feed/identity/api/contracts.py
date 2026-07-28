"""Version 1 HTTP contracts for the U02 identity and personalization boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]
ContentId = Annotated[str, StringConstraints(min_length=1, max_length=120)]
Email = Annotated[str, StringConstraints(min_length=3, max_length=320)]


class IdentityApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MessageResponse(IdentityApiModel):
    status: Literal["accepted", "completed"]
    message_key: str = Field(alias="messageKey")


class RegisterRequest(IdentityApiModel):
    email: Email
    password: Password


class TokenRequest(IdentityApiModel):
    token: Annotated[str, StringConstraints(min_length=20, max_length=2048)]


class LoginRequest(IdentityApiModel):
    email: Email
    password: Password
    device_label: Annotated[str, StringConstraints(min_length=1, max_length=120)] = Field(
        alias="deviceLabel"
    )


class LoginResponse(IdentityApiModel):
    user_id: UUID = Field(alias="userId")
    authorization_version: int = Field(alias="authorizationVersion", ge=1)


class PasswordResetRequest(IdentityApiModel):
    email: Email


class PasswordResetCompleteRequest(TokenRequest):
    new_password: Password = Field(alias="newPassword")


class ProfileUpdateRequest(IdentityApiModel):
    genres: dict[str, Literal["liked", "disliked"] | None] = Field(default_factory=dict)
    ott_subscriptions: dict[str, Literal["subscribed", "not_subscribed", "unspecified"]] = Field(
        default_factory=dict, alias="ottSubscriptions"
    )
    locale: Annotated[str, StringConstraints(min_length=2, max_length=20)] | None = None


class ProfileResponse(IdentityApiModel):
    profile_version: int = Field(alias="profileVersion", ge=1)
    genres: dict[str, str]
    ott_subscriptions: dict[str, str] = Field(alias="ottSubscriptions")
    locale: str


class RatingRequest(IdentityApiModel):
    rating: int = Field(ge=1, le=5)


class LibraryResponse(IdentityApiModel):
    row_version: int = Field(alias="rowVersion", ge=1)
    saved: list[str]
    ratings: dict[str, int]
    completed: list[str]


class ConsentRequest(IdentityApiModel):
    value: Literal["granted", "withdrawn"]
    policy_version: Annotated[str, StringConstraints(min_length=1, max_length=80)] = Field(
        alias="policyVersion"
    )
    notice_version: Annotated[str, StringConstraints(min_length=1, max_length=80)] = Field(
        alias="noticeVersion"
    )
    locale: Annotated[str, StringConstraints(min_length=2, max_length=20)] = "ko-KR"


class ConsentResponse(IdentityApiModel):
    decision_id: UUID = Field(alias="decisionId")
    consent_version: int = Field(alias="consentVersion", ge=1)
    value: str


class FeedbackRequest(IdentityApiModel):
    content_id: ContentId = Field(alias="contentId")
    event_type: Literal[
        "click",
        "dismiss",
        "ott_outbound",
        "save",
        "unsave",
        "rate",
        "unrate",
        "watch_complete",
    ] = Field(alias="eventType")
    source_surface: Annotated[str, StringConstraints(min_length=1, max_length=60)] = Field(
        alias="sourceSurface"
    )
    occurred_at: datetime = Field(alias="occurredAt")
    attributes: dict[str, str | int | bool] = Field(default_factory=dict)
    idempotency_key: Annotated[str, StringConstraints(min_length=8, max_length=120)] | None = Field(
        default=None, alias="idempotencyKey"
    )
    recommendation_version: str | None = Field(default=None, alias="recommendationVersion")


class FeedbackResponse(IdentityApiModel):
    event_id: UUID = Field(alias="eventId")
    created: bool


class DataRightsRequestBody(IdentityApiModel):
    idempotency_key: Annotated[str, StringConstraints(min_length=8, max_length=120)] = Field(
        alias="idempotencyKey"
    )


class DataRightsResponse(IdentityApiModel):
    request_id: UUID = Field(alias="requestId")
    status: str
    status_version: int = Field(alias="statusVersion", ge=1)


class CsrfResponse(IdentityApiModel):
    csrf_token: str = Field(alias="csrfToken")
