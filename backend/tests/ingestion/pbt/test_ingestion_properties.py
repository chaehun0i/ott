from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

from ott_feed.ingestion.application.normalization import MetadataNormalizer, normalize_text
from ott_feed.ingestion.application.raw import RawEnvelopeCodec
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
