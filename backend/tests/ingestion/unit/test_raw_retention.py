from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.ingestion.application.raw import RawEnvelopeCodec, RawObservationFactory
from ott_feed.ingestion.application.retention import expire_raw_body, select_expiry_batch
from ott_feed.ingestion.domain.models import TombstoneKind
from ott_feed.ingestion.ports import ProviderRecordEnvelope

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def observation(record_id: str, payload: bytes = b"{}"):
    return RawObservationFactory().create(
        raw_record_id=record_id,
        job_id="job-1",
        provider_id="provider-1",
        policy_id="policy-1",
        retention_seconds=60,
        envelope=ProviderRecordEnvelope(record_id, payload, NOW),
    )


def test_observation_digest_and_tombstone_are_stable() -> None:
    left = observation("raw-1", b'{"_tombstone":"content"}')
    right = observation("raw-2", b'{"_tombstone":"content"}')
    assert left.payload_digest == right.payload_digest
    assert left.tombstone_kind is TombstoneKind.CONTENT


def test_expiry_removes_only_body_and_is_idempotent() -> None:
    record = observation("raw-1", b"licensed")
    expired = expire_raw_body(record, NOW + timedelta(seconds=60))
    assert expired.payload_body is None
    assert expired.payload_digest == record.payload_digest
    assert expired.policy_id == record.policy_id
    assert expire_raw_body(expired, NOW + timedelta(days=1)) == expired


def test_retention_selection_is_bounded_and_ordered() -> None:
    records = (observation("b"), observation("a"), observation("c"))
    selected = select_expiry_batch(records, NOW + timedelta(seconds=60), 2)
    assert [item.raw_record_id for item in selected] == ["a", "b"]
    with pytest.raises(ValueError):
        select_expiry_batch(records, NOW, 0)


def test_codec_rejects_tampering() -> None:
    codec = RawEnvelopeCodec()
    encoded = codec.encode("provider-1", ProviderRecordEnvelope("record-1", b"body", NOW))
    with pytest.raises(ValueError):
        codec.decode(encoded.replace(b"Ym9keQ==", b"ZXZpbA=="))
