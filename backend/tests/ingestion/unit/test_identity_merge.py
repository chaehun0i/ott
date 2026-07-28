from datetime import UTC, datetime, timedelta

from ott_feed.ingestion.application.identity import IdentityResolver
from ott_feed.ingestion.application.merge import MergeEngine, should_withdraw
from ott_feed.ingestion.domain.models import IdentityDecision, NormalizedMetadata

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def normalized(identifier: str, title: str, normalized_id: str) -> NormalizedMetadata:
    return NormalizedMetadata(
        normalized_id,
        f"raw-{normalized_id}",
        "v1",
        "movie",
        (("imdb", identifier),),
        (("ko-KR", title),),
        60,
        ("comedy",),
        ("external_ids.imdb", "titles.ko-KR"),
    )


def test_identity_uses_first_decisive_tier_and_quarantines_ambiguity() -> None:
    value = normalized("tt1", "제목", "n1")
    matched = IdentityResolver(
        ("imdb",), {("imdb", "tt1"): frozenset({"content-1"})}, lambda: "new"
    ).resolve(value, "r1")
    assert matched.decision is IdentityDecision.MATCHED
    ambiguous = IdentityResolver(
        ("imdb",), {("imdb", "tt1"): frozenset({"a", "b"})}, lambda: "new"
    ).resolve(value, "r2")
    assert ambiguous.decision is IdentityDecision.AMBIGUOUS
    assert ambiguous.selected_content_id is None


def test_merge_prefers_authority_then_freshness_and_preserves_alternative() -> None:
    low = normalized("tt1", "낮음", "low")
    high = normalized("tt1", "높음", "high")
    merged = MergeEngine({"low": 1, "high": 10}).merge(
        merged_id="m1",
        canonical_content_id="content-1",
        inputs=(("low", NOW + timedelta(days=1), low), ("high", NOW, high)),
        computed_at=NOW,
    )
    title = next(item for item in merged.selected_fields if item.path == "title.ko-KR")
    assert title.value == "높음"
    assert any(item.value == "낮음" for item in merged.alternative_fields)


def test_tombstone_requires_last_authoritative_source() -> None:
    assert not should_withdraw("a", frozenset({"a", "b"}))
    assert should_withdraw("a", frozenset({"a"}))
