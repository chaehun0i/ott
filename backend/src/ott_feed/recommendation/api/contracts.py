"""Bounded U05 HTTP contracts."""

from pydantic import BaseModel, ConfigDict, Field


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4096)
    locale: str = Field(pattern="^(ko-KR|en-US)$")
    session_id: str | None = Field(default=None, max_length=120)
    expected_version: int | None = Field(default=None, ge=0)


class RecommendationItemContract(BaseModel):
    content_id: str
    title: str
    summary: str
    reason: str
    score: float
    metadata_version: str


class RecommendationContract(BaseModel):
    request_id: str
    intent_version: str
    confirmation_required: bool
    degraded_reasons: list[str]
    items: list[RecommendationItemContract]


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=0)
