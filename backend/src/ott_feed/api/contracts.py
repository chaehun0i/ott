"""Versioned Pydantic API contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ApiError(ApiModel):
    code: str
    message: str
    correlation_id: str = Field(alias="correlationId")
    retryable: bool = False
    details: dict[str, Any] | None = None


class ErrorEnvelope(ApiModel):
    error: ApiError


class CursorPageMeta(ApiModel):
    page_size: int = Field(alias="pageSize", ge=1, le=100)
    next_cursor: str | None = Field(default=None, alias="nextCursor")


class NumberedPageMeta(ApiModel):
    page: int = Field(ge=1)
    page_size: int = Field(alias="pageSize", ge=1, le=100)
    total: int = Field(ge=0)
