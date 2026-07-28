from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.catalog.application.closure import ApprovedClosureGuard
from ott_feed.catalog.application.detail import DetailQueryService
from ott_feed.catalog.application.feed import FeedQueryService
from ott_feed.catalog.config import CatalogSettings
from ott_feed.catalog.domain.errors import ApprovalClosureError, CatalogError
from ott_feed.catalog.domain.feed import build_feed, membership, query_fingerprint
from ott_feed.catalog.domain.localization import select_localization
from ott_feed.catalog.domain.models import (
    Availability,
    CatalogContent,
    CatalogSource,
    CatalogState,
    CatalogVersion,
    GenerationState,
    Localization,
    ProjectionGeneration,
)
from ott_feed.catalog.domain.policies import FeedFilters, freshness_state, matches_filters

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def content(content_id: str = "c1") -> CatalogContent:
    return CatalogContent(
        id=content_id,
        content_type="movie",
        genres=frozenset({"comedy"}),
        release_at=NOW - timedelta(days=1),
        runtime_minutes=55,
        popularity=0.9,
        localizations={
            "ko-KR": Localization("ko-KR", "웃기는 밤", "가벼운 코미디", ("배우 A",)),
            "en-US": Localization("en-US", "Funny Night", "A light comedy"),
        },
        availability=(
            Availability(
                "KR",
                "netflix",
                NOW,
                NOW - timedelta(days=2),
                NOW + timedelta(days=7),
                direct_url="https://example.test/watch/c1",
            ),
        ),
        source=CatalogSource("source", "record-1", "license-1", NOW),
        version=CatalogVersion(1),
        last_decision_id="decision-1",
    )


class Reader:
    def __init__(self, value: CatalogContent | None, *, fail: bool = False) -> None:
        self.value = value
        self.fail = fail

    def get_approved(self, content_id: str, region: str) -> CatalogContent | None:
        if self.fail:
            raise RuntimeError("database unavailable")
        return self.value if self.value and self.value.id == content_id else None


def test_catalog_invariants_transitions_and_generation() -> None:
    original = content()
    newer = original.replaced(content(), "decision-2")
    assert newer.version.value == 2 and newer.revision == 2
    newer.withdraw("decision-3")
    assert newer.state.value == CatalogState.WITHDRAWN.value
    newer.withdraw("decision-3")
    assert newer.version.value == 3
    newer.reactivate("decision-4")
    assert newer.state.value == CatalogState.APPROVED.value

    generation = ProjectionGeneration("g1", "feed", newer.version)
    generation.validate()
    generation.activate()
    assert generation.state is GenerationState.ACTIVE
    with pytest.raises(CatalogError):
        generation.fail()


def test_feed_filter_localization_freshness_and_detail() -> None:
    item = content()
    filters = FeedFilters(genres=frozenset({"comedy"}), providers=frozenset({"netflix"}))
    assert matches_filters(item, filters, "kr", NOW)
    assert membership(item, NOW) == {"new", "popular", "leaving_soon"}
    entries = build_feed([item, item], filters, "KR", NOW)
    assert len(entries) == 3
    assert query_fingerprint("KR", "ko-KR", filters) == query_fingerprint("kr", "ko-KR", filters)
    localized = select_localization(item.localizations, "ko", "en-US")
    assert localized.actual_locale == "ko-KR" and localized.fallback
    assert freshness_state(NOW - timedelta(hours=25), NOW) == "stale"

    closure = ApprovedClosureGuard(Reader(item))
    page = FeedQueryService(closure).query(
        [item],
        filters=filters,
        region="KR",
        locale="ko-KR",
        fallback_locale="en-US",
        now=NOW,
        generation="g1",
        limit=2,
    )
    assert len(page.items) == 2 and page.next_cursor is not None
    detail = DetailQueryService(closure).get(
        item.id, region="KR", locale="fr-FR", fallback_locale="en-US", now=NOW
    )
    assert detail.actual_locale == "en-US"
    assert detail.watch_urls == ("https://example.test/watch/c1",)


def test_closure_fails_closed_and_settings_validate() -> None:
    with pytest.raises(ApprovalClosureError, match="approved"):
        ApprovedClosureGuard(Reader(None)).require("missing", "KR", NOW)
    with pytest.raises(ApprovalClosureError, match="approved"):
        ApprovedClosureGuard(Reader(content(), fail=True)).require("c1", "KR", NOW)
    with pytest.raises(ValueError):
        CatalogSettings(max_page_size=0)
