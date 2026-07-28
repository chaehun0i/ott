from __future__ import annotations

from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ott_feed.catalog.domain.feed import build_feed
from ott_feed.catalog.domain.localization import select_localization
from ott_feed.catalog.domain.models import FeedCursor
from ott_feed.catalog.domain.policies import FeedFilters, active_availability, freshness_state
from ott_feed.search.adapters.security import CursorSigner
from tests.strategies.catalog import NOW, catalog_contents

pytestmark = pytest.mark.pbt


@given(catalog_contents())
def test_pbt_u03_01_closure_availability_is_exact_region(content) -> None:
    assert active_availability(content, "KR", NOW)
    assert not active_availability(content, "US", NOW)


@given(catalog_contents(), st.sampled_from(["comedy", "drama", "action"]))
def test_pbt_u03_02_filter_oracle(content, genre: str) -> None:
    result = build_feed([content], FeedFilters(genres=frozenset({genre})), "KR", NOW)
    assert bool(result) == (
        genre in content.genres and bool(build_feed([content], FeedFilters(), "KR", NOW))
    )


@given(st.lists(catalog_contents(), min_size=1, max_size=20))
def test_pbt_u03_03_dedup_and_deterministic_order(contents) -> None:
    left = build_feed(contents + contents, FeedFilters(), "KR", NOW)
    right = build_feed(list(reversed(contents)), FeedFilters(), "KR", NOW)
    assert [(x.section, x.content.id, x.score) for x in left] == [
        (x.section, x.content.id, x.score) for x in right
    ]


@given(st.text(alphabet="abc123", min_size=1), st.floats(allow_nan=False, allow_infinity=False))
def test_pbt_u03_04_cursor_round_trip(content_id: str, score: float) -> None:
    signer = CursorSigner(b"k" * 32)
    cursor = FeedCursor("fp", "g1", score, content_id)
    assert signer.decode(signer.encode(cursor)) == cursor


@given(st.lists(st.integers(min_value=0, max_value=1000), unique=True, max_size=50))
def test_pbt_u03_05_keyset_pages_do_not_overlap(values: list[int]) -> None:
    ordered = sorted(values)
    split = len(ordered) // 2
    assert set(ordered[:split]).isdisjoint(ordered[split:])
    assert ordered[:split] + ordered[split:] == ordered


@given(catalog_contents(), st.integers(min_value=-100, max_value=100))
def test_pbt_u03_06_availability_window(content, offset: int) -> None:
    active = active_availability(content, "KR", NOW + timedelta(days=offset))
    assert bool(active) == (-1 <= offset < 5)


@given(catalog_contents(), st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=2, max_size=5))
def test_pbt_u03_07_locale_fallback_reports_actual(content, language: str) -> None:
    selected = select_localization(content.localizations, language, "ko-KR")
    assert selected.actual_locale in content.localizations
    assert selected.value == content.localizations[selected.actual_locale]


@given(st.integers(min_value=0, max_value=72))
def test_pbt_u03_08_freshness_boundary(hours: int) -> None:
    expected = "fresh" if hours <= 24 else "stale"
    assert freshness_state(NOW - timedelta(hours=hours), NOW) == expected


class ProjectionReferenceMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.received: set[int] = set()
        self.contiguous = 0

    @rule(version=st.integers(min_value=1, max_value=30))
    def receive(self, version: int) -> None:
        self.received.add(version)
        while self.contiguous + 1 in self.received:
            self.contiguous += 1

    @invariant()
    def contiguous_prefix_only(self) -> None:
        assert all(version in self.received for version in range(1, self.contiguous + 1))


TestProjectionReference = ProjectionReferenceMachine.TestCase
