from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

from ott_feed.ingestion.application.identity import IdentityResolver
from ott_feed.ingestion.application.merge import MergeEngine, should_withdraw
from ott_feed.ingestion.application.normalization import MetadataNormalizer, normalize_text
from ott_feed.ingestion.application.raw import RawEnvelopeCodec
from ott_feed.ingestion.domain.models import IdentityDecision, NormalizedMetadata
from ott_feed.ingestion.ports import ProviderRecordEnvelope


@given(
    provider_id=st.text(min_size=1, max_size=40),
    record_id=st.text(min_size=1, max_size=80),
    payload=st.binary(max_size=512),
    timestamp=st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2035, 1, 1),
        timezones=st.just(UTC),
    ),
)
def test_p_u04_01_raw_codec_round_trip(
    provider_id: str, record_id: str, payload: bytes, timestamp: datetime
) -> None:
    codec = RawEnvelopeCodec()
    original = ProviderRecordEnvelope(record_id, payload, timestamp)
    decoded_provider, decoded, digest = codec.decode(codec.encode(provider_id, original))
    assert decoded_provider == provider_id
    assert decoded == original
    assert len(digest) == 64


@given(value=st.text(max_size=300))
def test_p_u04_02_normalization_is_idempotent(value: str) -> None:
    assert normalize_text(normalize_text(value)) == normalize_text(value)


@given(
    identifiers=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=40).filter(str.strip),
        max_size=8,
    )
)
def test_p_u04_03_normalization_preserves_identifier_sources(
    identifiers: dict[str, str],
) -> None:
    result = MetadataNormalizer().normalize(
        {"external_ids": identifiers}, raw_record_id="raw", normalized_id="normalized"
    )
    normalized_input = {
        key: normalize_text(value) for key, value in identifiers.items() if normalize_text(value)
    }
    assert dict(result.identifiers) == normalized_input
    assert {path.removeprefix("external_ids.") for path in result.source_paths} == set(
        normalized_input
    )


def _normalized(normalized_id: str, value: str) -> NormalizedMetadata:
    return NormalizedMetadata(
        normalized_id,
        f"raw-{normalized_id}",
        "v1",
        "movie",
        (("imdb", value),),
        (("en-US", value),),
        60,
        (),
        ("external_ids.imdb", "titles.en-US"),
    )


@given(candidates=st.sets(st.text(min_size=1, max_size=20), max_size=4))
def test_p_u04_04_identity_matches_reference_oracle(candidates: set[str]) -> None:
    resolver = IdentityResolver(
        ("imdb",), {("imdb", "tt1"): frozenset(candidates)}, lambda: "new-content"
    )
    result = resolver.resolve(_normalized("n1", "tt1"), "resolution")
    expected = (
        IdentityDecision.NEW
        if not candidates
        else IdentityDecision.MATCHED
        if len(candidates) == 1
        else IdentityDecision.AMBIGUOUS
    )
    assert result.decision is expected


@given(order=st.permutations(("a", "b", "c")))
def test_p_u04_05_merge_is_commutative(order: list[str]) -> None:
    values = {name: _normalized(name, f"title-{name}") for name in order}
    engine = MergeEngine({"a": 1, "b": 2, "c": 3})
    inputs = tuple((name, datetime(2026, 1, 1, tzinfo=UTC), values[name]) for name in order)
    result = engine.merge(
        merged_id="merged",
        canonical_content_id="content",
        inputs=inputs,
        computed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert tuple((item.path, item.value) for item in result.selected_fields) == (
        ("identifier.imdb", "title-c"),
        ("runtime_minutes", "60"),
        ("title.en-US", "title-c"),
    )


@given(values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=8))
def test_p_u04_06_merge_preserves_every_candidate(values: list[str]) -> None:
    inputs = tuple(
        (f"p{i}", datetime(2026, 1, 1, tzinfo=UTC), _normalized(f"n{i}", value))
        for i, value in enumerate(values)
    )
    result = MergeEngine({f"p{i}": i for i in range(len(values))}).merge(
        merged_id="m",
        canonical_content_id="c",
        inputs=inputs,
        computed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    candidates = result.selected_fields + result.alternative_fields
    assert len([item for item in candidates if item.path == "title.en-US"]) == len(values)


@given(
    active=st.sets(st.text(min_size=1, max_size=10), max_size=8),
    removed=st.text(min_size=1, max_size=10),
)
def test_p_u04_11_tombstone_never_removes_another_valid_source(
    active: set[str], removed: str
) -> None:
    assert should_withdraw(removed, frozenset(active)) is (not (active - {removed}))
