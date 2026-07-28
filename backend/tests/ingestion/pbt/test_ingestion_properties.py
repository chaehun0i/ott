from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

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
