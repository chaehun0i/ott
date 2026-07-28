"""Release compatibility, backup manifest and restore verification services."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ott_feed.platform.domain.errors import invalid_state
from ott_feed.platform.domain.models import (
    ApiContractVersion,
    BackupRecord,
    DeploymentRecord,
    ReleaseArtifact,
    RestoreAttempt,
)


@dataclass(frozen=True, slots=True)
class CompatibilityEvidence:
    openapi_compatible: bool
    migration_expand_only: bool
    tests_passed: bool
    scans_passed: bool

    @property
    def accepted(self) -> bool:
        return all(
            (
                self.openapi_compatible,
                self.migration_expand_only,
                self.tests_passed,
                self.scans_passed,
            )
        )


def create_release(
    release_id: str,
    git_revision: str,
    release_tag: str,
    image_digest: str,
    contract: ApiContractVersion,
    evidence: CompatibilityEvidence,
) -> ReleaseArtifact:
    return ReleaseArtifact(
        release_id,
        git_revision,
        release_tag,
        image_digest,
        contract,
        evidence.accepted,
    )


def plan_deployment(artifact: ReleaseArtifact, previous_digest: str | None) -> DeploymentRecord:
    if not artifact.deployable:
        raise invalid_state("release_blocked", "Release evidence did not pass")
    return DeploymentRecord(artifact=artifact, previous_digest=previous_digest)


@dataclass(frozen=True, slots=True)
class BackupManifest:
    object_key: str
    source_release: str
    schema_version: str
    created_at: datetime
    checksum: str
    encrypted: bool


def create_backup_record(
    payload: bytes, object_key: str, release: str, schema: str
) -> tuple[BackupRecord, BackupManifest]:
    now = datetime.now(UTC)
    checksum = hashlib.sha256(payload).hexdigest()
    manifest = BackupManifest(object_key, release, schema, now, checksum, True)
    record = BackupRecord(object_key)
    record.mark_uploaded(checksum, encrypted=True, expires_at=now + timedelta(days=30))
    record.verify()
    return record, manifest


SmokeAssertion = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class RecoveryMeasurement:
    recovery_seconds: float
    data_age_seconds: float
    meets_rto: bool
    meets_rpo: bool


def measure_recovery(
    started_at: datetime, finished_at: datetime, backup_created_at: datetime
) -> RecoveryMeasurement:
    recovery = max(0.0, (finished_at - started_at).total_seconds())
    data_age = max(0.0, (started_at - backup_created_at).total_seconds())
    return RecoveryMeasurement(recovery, data_age, recovery <= 4 * 3600, data_age <= 24 * 3600)


class RestoreVerifier:
    def __init__(self, assertions: Iterable[SmokeAssertion]) -> None:
        self.assertions = tuple(assertions)

    def verify(
        self, attempt: RestoreAttempt, actual_checksum: str, manifest: BackupManifest
    ) -> RestoreAttempt:
        attempt.mark_loaded()
        attempt.verify_integrity(actual_checksum == manifest.checksum and manifest.encrypted)
        if not attempt.integrity_ok:
            return attempt
        attempt.verify_smoke(
            bool(self.assertions) and all(assertion() for assertion in self.assertions)
        )
        return attempt
