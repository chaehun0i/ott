"""U06 API contracts."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NotificationView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notification_id: str
    content_id: str
    event_type: str
    channel: str
    created_at: str


class OverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: Annotated[int, Field(ge=0)]
    patch: dict[str, object]
    idempotency_key: Annotated[str, Field(min_length=8, max_length=160)]


class TraceView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    policy_versions: dict[str, str] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list, max_length=100)
    outcome: str | None = None


class IncidentView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str
    severity: str
    state: str
    version: int
