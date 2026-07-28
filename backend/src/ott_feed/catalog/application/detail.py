"""Localized approved-content detail query."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.catalog.application.closure import ApprovedClosureGuard
from ott_feed.catalog.domain.localization import select_localization
from ott_feed.catalog.domain.policies import active_availability, freshness_state


@dataclass(frozen=True, slots=True)
class ContentDetail:
    content_id: str
    title: str
    synopsis: str
    requested_locale: str
    actual_locale: str
    providers: tuple[str, ...]
    watch_urls: tuple[str, ...]
    source_provider: str
    source_record_id: str
    freshness: str
    catalog_version: int


class DetailQueryService:
    def __init__(self, closure: ApprovedClosureGuard) -> None:
        self.closure = closure

    def get(
        self,
        content_id: str,
        *,
        region: str,
        locale: str,
        fallback_locale: str,
        now: datetime,
    ) -> ContentDetail:
        content = self.closure.require(content_id, region, now)
        localized = select_localization(content.localizations, locale, fallback_locale)
        availability = active_availability(content, region, now)
        return ContentDetail(
            content_id=content.id,
            title=localized.value.title,
            synopsis=localized.value.synopsis,
            requested_locale=locale,
            actual_locale=localized.actual_locale,
            providers=tuple(item.provider for item in availability),
            watch_urls=tuple(item.preferred_url for item in availability),
            source_provider=content.source.provider,
            source_record_id=content.source.source_record_id,
            freshness=freshness_state(content.source.last_success_at, now),
            catalog_version=content.version.value,
        )
