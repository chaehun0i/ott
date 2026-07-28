"""Pure filtering, freshness and lawful availability policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ott_feed.catalog.domain.models import Availability, CatalogContent, CatalogState


@dataclass(frozen=True, slots=True)
class FeedFilters:
    content_types: frozenset[str] = frozenset()
    genres: frozenset[str] = frozenset()
    providers: frozenset[str] = frozenset()
    max_runtime_minutes: int | None = None


def active_availability(
    content: CatalogContent, region: str, instant: datetime
) -> tuple[Availability, ...]:
    return tuple(
        item
        for item in content.availability
        if item.region.upper() == region.upper() and item.active_at(instant)
    )


def matches_filters(
    content: CatalogContent, filters: FeedFilters, region: str, instant: datetime
) -> bool:
    if content.state is not CatalogState.APPROVED:
        return False
    available = active_availability(content, region, instant)
    if not available:
        return False
    if filters.content_types and content.content_type not in filters.content_types:
        return False
    if filters.genres and content.genres.isdisjoint(filters.genres):
        return False
    if filters.providers and not any(item.provider in filters.providers for item in available):
        return False
    return not (
        filters.max_runtime_minutes is not None
        and (
            content.runtime_minutes is None or content.runtime_minutes > filters.max_runtime_minutes
        )
    )


def freshness_state(
    last_success_at: datetime, now: datetime, threshold: timedelta = timedelta(hours=24)
) -> str:
    return "fresh" if now - last_success_at <= threshold else "stale"
