from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.ingestion.application.raw import RawObservationFactory
from ott_feed.ingestion.application.recovery import RecoveryCoordinator, RecoverySnapshot
from ott_feed.ingestion.application.retention import expire_raw_body
from ott_feed.ingestion.domain.errors import IngestionError
from ott_feed.ingestion.ports import ProviderRecordEnvelope

pytestmark = pytest.mark.integration
NOW = datetime(2026, 7, 28, tzinfo=UTC)


def test_payload_expiry_and_restore_inconsistency_fail_closed() -> None:
    record = RawObservationFactory().create(
        raw_record_id="raw",
        job_id="job",
        provider_id="provider",
        policy_id="policy",
        retention_seconds=1,
        envelope=ProviderRecordEnvelope("record", b"licensed", NOW),
    )
    assert expire_raw_body(record, NOW + timedelta(seconds=1)).payload_body is None
    with pytest.raises(IngestionError, match="expired_raw_bodies"):
        RecoveryCoordinator().verify(RecoverySnapshot(expired_raw_bodies=1))
