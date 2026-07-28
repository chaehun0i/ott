from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.platform.application.delivery import (
    BackupManifest,
    CompatibilityEvidence,
    RestoreVerifier,
    create_backup_record,
    create_release,
    plan_deployment,
)
from ott_feed.platform.application.idempotency import (
    IdempotencyService,
    MemoryIdempotencyRepository,
)
from ott_feed.platform.application.pagination import CursorCodec, filter_fingerprint
from ott_feed.platform.domain.errors import PlatformError
from ott_feed.platform.domain.models import (
    ApiContractVersion,
    CursorToken,
    JobStatus,
    OutboxJob,
    RestoreAttempt,
)
from ott_feed.platform.telemetry import redact


def test_idempotency_replays_completed_result_and_rejects_changed_payload() -> None:
    service = IdempotencyService(MemoryIdempotencyRepository())
    record = service.reserve("notification", "key-1", {"content": "c1"})
    service.complete(record, 202, {"jobId": "j1"})
    replay = service.reserve("notification", "key-1", {"content": "c1"})
    assert replay.response_body == {"jobId": "j1"}
    with pytest.raises(PlatformError, match="payload differs"):
        service.reserve("notification", "key-1", {"content": "c2"})


def test_cursor_rejects_filter_mismatch() -> None:
    codec = CursorCodec(b"0123456789abcdef")
    expected = filter_fingerprint({"ott": "netflix"})
    token = codec.encode(CursorToken("2026-01-01", "id-1", expected))
    assert codec.decode(token, expected).tie_breaker == "id-1"
    with pytest.raises(PlatformError, match="does not match"):
        codec.decode(token, filter_fingerprint({"ott": "other"}))


def test_outbox_terminal_state_and_authorized_requeue() -> None:
    job = OutboxJob("notification.send", {"user": "u1"}, max_attempts=1)
    job.claim("worker-1", timedelta(seconds=30))
    job.fail("worker-1", "provider_failed")
    assert job.status == JobStatus.DEAD_LETTER
    replacement = job.requeue("operator approved")
    assert replacement.previous_job_id == job.id
    assert replacement.status == JobStatus.PENDING


def test_us026_backup_restore_requires_integrity_and_smoke() -> None:
    record, manifest = create_backup_record(b"backup", "daily/backup.enc", "v1", "0001")
    assert record.encrypted and record.expires_at and record.expires_at > datetime.now(UTC)
    attempt = RestoreVerifier([lambda: True]).verify(
        RestoreAttempt(record.id), manifest.checksum, manifest
    )
    assert attempt.verified

    failed = RestoreVerifier([lambda: True]).verify(
        RestoreAttempt(record.id),
        "wrong-checksum",
        BackupManifest("key", "v1", "0001", datetime.now(UTC), "expected", True),
    )
    assert not failed.verified


def test_us028_release_gate_and_digest_rollback() -> None:
    evidence = CompatibilityEvidence(True, True, True, True)
    release = create_release("r1", "abc", "v1", "sha256:123", ApiContractVersion(1, "fp"), evidence)
    deployment = plan_deployment(release, "sha256:old")
    deployment.deploy()
    deployment.verify()
    deployment.rollback("sha256:old", database_compatible=True)
    assert deployment.previous_digest == "sha256:old"


def test_error_redaction_removes_secret_values_recursively() -> None:
    value = {"token": "raw", "nested": {"passwordHash": "raw", "safe": "ok"}}
    assert redact(value) == {
        "token": "[REDACTED]",
        "nested": {"passwordHash": "[REDACTED]", "safe": "ok"},
    }
