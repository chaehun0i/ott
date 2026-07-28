"""U07 aggregates and state machines described by BR-U07-001 through BR-U07-038."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from .errors import conflict, invalid_state


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class ApiContractVersion:
    major: int
    fingerprint: str

    def __post_init__(self) -> None:
        if self.major < 1 or not self.fingerprint:
            raise ValueError("contract version requires a positive major and fingerprint")

    def accepts(self, requested_major: int) -> bool:
        return requested_major == self.major


class IdempotencyStatus(StrEnum):
    RESERVED = "reserved"
    COMPLETED = "completed"
    RETRYABLE_FAILURE = "retryable_failure"


@dataclass(slots=True)
class IdempotencyRecord:
    scope: str
    key: str
    payload_hash: str
    status: IdempotencyStatus = IdempotencyStatus.RESERVED
    response_status: int | None = None
    response_body: dict[str, Any] | None = None

    def assert_payload(self, payload_hash: str) -> None:
        if payload_hash != self.payload_hash:
            raise conflict("idempotency_payload_conflict", "Idempotency key payload differs")

    def complete(self, status: int, body: dict[str, Any]) -> None:
        if self.status == IdempotencyStatus.COMPLETED:
            if status != self.response_status or body != self.response_body:
                raise conflict("idempotency_already_completed", "Completed result is immutable")
            return
        self.status = IdempotencyStatus.COMPLETED
        self.response_status = status
        self.response_body = body.copy()

    def mark_retryable_failure(self) -> None:
        if self.status == IdempotencyStatus.COMPLETED:
            raise invalid_state("completed_result_immutable", "Completed request cannot be retried")
        self.status = IdempotencyStatus.RETRYABLE_FAILURE


@dataclass(frozen=True, slots=True)
class CursorToken:
    position: str
    tie_breaker: str
    filter_fingerprint: str
    contract_version: int = 1


@dataclass(frozen=True, slots=True)
class CursorPage:
    items: tuple[Any, ...]
    page_size: int
    next_cursor: str | None = None

    def __post_init__(self) -> None:
        if self.page_size < 1 or len(self.items) > self.page_size:
            raise ValueError("cursor page exceeds its positive page size")


@dataclass(frozen=True, slots=True)
class NumberedPage:
    items: tuple[Any, ...]
    page: int
    page_size: int
    total: int

    def __post_init__(self) -> None:
        if self.page < 1 or self.page_size < 1 or self.total < 0:
            raise ValueError("page metadata is outside its valid range")
        if len(self.items) > self.page_size:
            raise ValueError("numbered page exceeds page size")


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RETRY_WAIT = "retry_wait"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


TERMINAL_JOB_STATES = {JobStatus.SUCCEEDED, JobStatus.CANCELLED}


@dataclass(slots=True)
class OutboxJob:
    job_type: str
    payload: dict[str, Any]
    lane: str = "normal"
    priority: int = 100
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 5
    lease_owner: str | None = None
    lease_until: datetime | None = None
    available_at: datetime = field(default_factory=utc_now)
    failure_code: str | None = None
    previous_job_id: UUID | None = None

    def claim(self, worker_id: str, lease_for: timedelta, now: datetime | None = None) -> None:
        now = now or utc_now()
        eligible = self.status in {JobStatus.PENDING, JobStatus.RETRY_WAIT}
        expired = (
            self.status == JobStatus.PROCESSING
            and self.lease_until is not None
            and self.lease_until <= now
        )
        if (not eligible and not expired) or self.available_at > now:
            raise conflict("job_not_claimable", "Job is not claimable")
        self.status = JobStatus.PROCESSING
        self.attempt_count += 1
        self.lease_owner = worker_id
        self.lease_until = now + lease_for

    def _assert_owner(self, worker_id: str) -> None:
        if self.status != JobStatus.PROCESSING or self.lease_owner != worker_id:
            raise conflict("job_lease_conflict", "Worker does not own the active lease")

    def complete(self, worker_id: str) -> None:
        self._assert_owner(worker_id)
        self.status = JobStatus.SUCCEEDED
        self.lease_owner = None
        self.lease_until = None

    def fail(self, worker_id: str, code: str, retry_at: datetime | None = None) -> None:
        self._assert_owner(worker_id)
        self.failure_code = code
        self.lease_owner = None
        self.lease_until = None
        if retry_at is not None and self.attempt_count < self.max_attempts:
            self.status = JobStatus.RETRY_WAIT
            self.available_at = retry_at
        else:
            self.status = JobStatus.DEAD_LETTER

    def cancel(self) -> None:
        if self.status in TERMINAL_JOB_STATES:
            raise invalid_state("terminal_job_immutable", "Terminal job cannot change state")
        self.status = JobStatus.CANCELLED

    def requeue(self, reason: str) -> OutboxJob:
        if self.status != JobStatus.DEAD_LETTER or not reason.strip():
            raise invalid_state("job_not_requeueable", "Dead-letter job and reason are required")
        return OutboxJob(
            job_type=self.job_type,
            payload={**self.payload, "requeueReason": reason},
            lane=self.lane,
            priority=self.priority,
            max_attempts=self.max_attempts,
            previous_job_id=self.id,
        )


@dataclass(frozen=True, slots=True)
class ReleaseArtifact:
    release_id: str
    git_revision: str
    release_tag: str
    image_digest: str
    contract_version: ApiContractVersion
    migration_compatible: bool

    @property
    def deployable(self) -> bool:
        return (
            bool(self.git_revision and self.image_digest.startswith("sha256:"))
            and self.migration_compatible
        )


class DeploymentStatus(StrEnum):
    PLANNED = "planned"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass(slots=True)
class DeploymentRecord:
    artifact: ReleaseArtifact
    status: DeploymentStatus = DeploymentStatus.PLANNED
    previous_digest: str | None = None

    def deploy(self) -> None:
        if not self.artifact.deployable:
            raise invalid_state("release_not_deployable", "Release compatibility gate failed")
        self.status = DeploymentStatus.DEPLOYED

    def verify(self) -> None:
        if self.status != DeploymentStatus.DEPLOYED:
            raise invalid_state("deployment_not_active", "Only a deployed release can be verified")
        self.status = DeploymentStatus.VERIFIED

    def rollback(self, target_digest: str, database_compatible: bool) -> None:
        if not database_compatible or not target_digest.startswith("sha256:"):
            raise invalid_state("rollback_not_compatible", "Rollback target is not compatible")
        self.previous_digest = target_digest
        self.status = DeploymentStatus.ROLLED_BACK


class BackupStatus(StrEnum):
    STARTED = "started"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass(slots=True)
class BackupRecord:
    object_key: str
    id: UUID = field(default_factory=uuid4)
    status: BackupStatus = BackupStatus.STARTED
    checksum: str | None = None
    encrypted: bool = False
    expires_at: datetime | None = None
    failure_code: str | None = None

    def mark_uploaded(self, checksum: str, encrypted: bool, expires_at: datetime) -> None:
        if not checksum or not encrypted or expires_at <= utc_now():
            raise invalid_state("invalid_backup_artifact", "Backup artifact is incomplete")
        self.checksum = checksum
        self.encrypted = encrypted
        self.expires_at = expires_at
        self.status = BackupStatus.UPLOADED

    def verify(self) -> None:
        if self.status != BackupStatus.UPLOADED or not self.checksum or not self.encrypted:
            raise invalid_state("backup_not_verifiable", "Uploaded encrypted backup is required")
        self.status = BackupStatus.VERIFIED

    def fail(self, code: str) -> None:
        self.failure_code = code
        self.status = BackupStatus.FAILED


class RestoreStatus(StrEnum):
    CREATED = "created"
    LOADED = "loaded"
    INTEGRITY_PASSED = "integrity_passed"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass(slots=True)
class RestoreAttempt:
    backup_id: UUID
    id: UUID = field(default_factory=uuid4)
    previous_attempt_id: UUID | None = None
    status: RestoreStatus = RestoreStatus.CREATED
    integrity_ok: bool = False
    smoke_ok: bool = False
    failure_code: str | None = None

    def mark_loaded(self) -> None:
        if self.status != RestoreStatus.CREATED:
            raise invalid_state("restore_load_order", "Restore can only load once")
        self.status = RestoreStatus.LOADED

    def verify_integrity(self, passed: bool) -> None:
        if self.status != RestoreStatus.LOADED or not passed:
            self.fail("integrity_failed")
            return
        self.integrity_ok = True
        self.status = RestoreStatus.INTEGRITY_PASSED

    def verify_smoke(self, passed: bool) -> None:
        if self.status != RestoreStatus.INTEGRITY_PASSED or not passed:
            self.fail("smoke_failed")
            return
        self.smoke_ok = True
        self.status = RestoreStatus.VERIFIED

    def fail(self, code: str) -> None:
        self.failure_code = code
        self.status = RestoreStatus.FAILED

    @property
    def verified(self) -> bool:
        return self.status == RestoreStatus.VERIFIED and self.integrity_ok and self.smoke_ok
