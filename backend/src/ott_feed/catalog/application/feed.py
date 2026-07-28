"""Snapshot feed query with deterministic keyset pagination and final closure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.catalog.application.closure import ApprovedClosureGuard
from ott_feed.catalog.domain.errors import CatalogError
from ott_feed.catalog.domain.feed import FeedEntry, build_feed, query_fingerprint
from ott_feed.catalog.domain.localization import select_localization
from ott_feed.catalog.domain.models import CatalogContent, FeedCursor
from ott_feed.catalog.domain.policies import FeedFilters, active_availability, freshness_state


@dataclass(frozen=True, slots=True)
class FeedItem:
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


@dataclass(frozen=True, slots=True)
class FeedPage:
    items: tuple[FeedItem, ...]
    next_cursor: FeedCursor | None
    generation: str
    fingerprint: str


class FeedQueryService:
    def __init__(self, closure: ApprovedClosureGuard, *, max_page_size: int = 50) -> None:
        self.closure = closure
        self.max_page_size = max_page_size

    def query(
        self,
        contents: list[CatalogContent],
        *,
        filters: FeedFilters,
        region: str,
        locale: str,
        fallback_locale: str,
        now: datetime,
        generation: str,
        limit: int = 20,
        after: FeedCursor | None = None,
    ) -> FeedPage:
        if not region:
            raise CatalogError("FEED_REGION_REQUIRED", "region is required")
        if not 1 <= limit <= self.max_page_size:
            raise CatalogError("FEED_PAGE_LIMIT", "page size is outside the supported range")
        fingerprint = query_fingerprint(region, locale, filters)
        if after is not None and (
            after.fingerprint != fingerprint or after.generation != generation
        ):
            raise CatalogError("FEED_CURSOR_MISMATCH", "cursor query or generation mismatch")
        entries = build_feed(contents, filters, region, now)
        if after is not None:
            entries = [
                entry
                for entry in entries
                if (-entry.score, entry.content.id) > (-after.score, after.content_id)
            ]
        visible: list[FeedItem] = []
        accepted_entries: list[FeedEntry] = []
        for entry in entries:
            try:
                current = self.closure.require(entry.content.id, region, now)
            except CatalogError:
                continue
            localization = select_localization(current.localizations, locale, fallback_locale)
            availability = active_availability(current, region, now)[0]
            visible.append(
                FeedItem(
                    content_id=current.id,
                    section=entry.section,
                    title=localization.value.title,
                    requested_locale=locale,
                    actual_locale=localization.actual_locale,
                    provider=availability.provider,
                    watch_url=availability.preferred_url,
                    freshness=freshness_state(current.source.last_success_at, now),
                    catalog_version=current.version.value,
                    score=entry.score,
                )
            )
            accepted_entries.append(entry)
            if len(visible) == limit:
                break
        cursor = None
        if len(visible) == limit and accepted_entries:
            last = accepted_entries[-1]
            cursor = FeedCursor(fingerprint, generation, last.score, last.content.id)
        return FeedPage(tuple(visible), cursor, generation, fingerprint)
