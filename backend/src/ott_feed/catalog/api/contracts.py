"""Versioned feed and detail response contracts."""

from pydantic import BaseModel, ConfigDict, Field


class FeedItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    content_id: str
    section: str
    title: str
    requested_locale: str
    actual_locale: str
    provider: str
    watch_url: str
    freshness: str
    catalog_version: int
    score: float


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")
    generation: str
    query_fingerprint: str = Field(alias="queryFingerprint")
    degraded_reason: str | None = Field(default=None, alias="degradedReason")


class DetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    content_id: str = Field(alias="contentId")
    title: str
    synopsis: str
    requested_locale: str = Field(alias="requestedLocale")
    actual_locale: str = Field(alias="actualLocale")
    providers: list[str]
    watch_urls: list[str] = Field(alias="watchUrls")
    source_provider: str = Field(alias="sourceProvider")
    source_record_id: str = Field(alias="sourceRecordId")
    freshness: str
    catalog_version: int = Field(alias="catalogVersion")
