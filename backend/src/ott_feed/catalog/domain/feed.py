"""Deterministic multi-section integrated-feed policy."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from ott_feed.catalog.domain.models import CatalogContent
from ott_feed.catalog.domain.policies import FeedFilters, matches_filters


@dataclass(frozen=True, slots=True)
class FeedEntry:
    content: CatalogContent
    section: str
    score: float


def membership(content: CatalogContent, now: datetime) -> frozenset[str]:
    sections: set[str] = set()
    delta = content.release_at - now
    if timedelta(0) <= delta <= timedelta(days=30):
        sections.add("upcoming")
    if timedelta(days=-30) <= delta < timedelta(0):
        sections.add("new")
    if content.popularity >= 0.7:
        sections.add("popular")
    if any(
        item.ends_at is not None and timedelta(0) < item.ends_at - now <= timedelta(days=14)
        for item in content.availability
    ):
        sections.add("leaving_soon")
    return frozenset(sections)


def feed_score(content: CatalogContent, now: datetime) -> float:
    age_days = max(0.0, (now - content.release_at).total_seconds() / 86400)
    freshness = max(0.0, 1.0 - age_days / 30)
    return round(content.popularity * 0.7 + freshness * 0.3, 8)


def build_feed(
    contents: list[CatalogContent], filters: FeedFilters, region: str, now: datetime
) -> list[FeedEntry]:
    deduplicated: dict[str, CatalogContent] = {}
    for item in contents:
        current = deduplicated.get(item.id)
        if current is None or (
            item.version.value,
            item.revision,
            item.last_decision_id,
            item.popularity,
            item.release_at,
        ) > (
            current.version.value,
            current.revision,
            current.last_decision_id,
            current.popularity,
            current.release_at,
        ):
            deduplicated[item.id] = item
    result = [
        FeedEntry(content, section, feed_score(content, now))
        for content in deduplicated.values()
        if matches_filters(content, filters, region, now)
        for section in sorted(membership(content, now))
    ]
    return sorted(result, key=lambda item: (item.section, -item.score, item.content.id))


def query_fingerprint(region: str, locale: str, filters: FeedFilters) -> str:
    canonical = json.dumps(
        {
            "region": region.upper(),
            "locale": locale,
            "content_types": sorted(filters.content_types),
            "genres": sorted(filters.genres),
            "providers": sorted(filters.providers),
            "max_runtime_minutes": filters.max_runtime_minutes,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
