"""Versioned natural-language search contracts."""

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    region: str = Field(min_length=2, max_length=8)
    locale: str = Field(default="ko-KR", min_length=2, max_length=20)
    page_size: int = Field(default=20, alias="pageSize", ge=1, le=50)

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class SearchItemResponse(BaseModel):
    content_id: str = Field(alias="contentId")
    title: str
    actual_locale: str = Field(alias="actualLocale")
    rank: int
    channels: list[str]


class SearchResponse(BaseModel):
    items: list[SearchItemResponse]
    degraded_reason: str | None = Field(default=None, alias="degradedReason")
    generation: str
