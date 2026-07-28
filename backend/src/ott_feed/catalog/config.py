"""Typed U03 catalog configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class CatalogSettings:
    default_locale: str = "ko-KR"
    fallback_locale: str = "en-US"
    default_freshness_hours: int = 24
    max_page_size: int = 50
    max_filter_values: int = 20
    statement_timeout_ms: int = 1500
    closure_timeout_ms: int = 300
    api_pool_size: int = 10
    worker_pool_size: int = 5

    def __post_init__(self) -> None:
        if not self.default_locale or not self.fallback_locale:
            raise ValueError("locales must not be empty")
        for name in (
            "default_freshness_hours",
            "max_page_size",
            "max_filter_values",
            "statement_timeout_ms",
            "closure_timeout_ms",
            "api_pool_size",
            "worker_pool_size",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    @classmethod
    def from_environment(cls) -> CatalogSettings:
        return cls(
            default_locale=os.getenv("CATALOG_DEFAULT_LOCALE", "ko-KR"),
            fallback_locale=os.getenv("CATALOG_FALLBACK_LOCALE", "en-US"),
            default_freshness_hours=_positive("CATALOG_FRESHNESS_HOURS", 24),
            max_page_size=_positive("CATALOG_MAX_PAGE_SIZE", 50),
            max_filter_values=_positive("CATALOG_MAX_FILTER_VALUES", 20),
            statement_timeout_ms=_positive("CATALOG_STATEMENT_TIMEOUT_MS", 1500),
            closure_timeout_ms=_positive("CATALOG_CLOSURE_TIMEOUT_MS", 300),
            api_pool_size=_positive("CATALOG_API_POOL_SIZE", 10),
            worker_pool_size=_positive("CATALOG_WORKER_POOL_SIZE", 5),
        )
