"""Lease-fenced U04 job lifecycle and reconciled page outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.ingestion.domain.errors import IllegalTransition, IngestionError
from ott_feed.ingestion.domain.models import IngestionJob, JobStatus


@dataclass(frozen=True, slots=True)
class ClaimToken:
    job_id: str
    worker_id: str
    claim_version: int


@dataclass(frozen=True, slots=True)
class PageOutcome:
    next_cursor: str | None
    succeeded: frozenset[str]
    quarantined: frozenset[str]
    failed: frozenset[str]

    def __post_init__(self) -> None:
        total = len(self.succeeded) + len(self.quarantined) + len(self.failed)
        union = self.succeeded | self.quarantined | self.failed
        if total != len(union):
            raise ValueError("record outcomes must be disjoint")

    @property
    def record_ids(self) -> frozenset[str]:
        return self.succeeded | self.quarantined | self.failed


class JobLifecycle:
    @staticmethod
    def token(job: IngestionJob) -> ClaimToken:
        if job.status is not JobStatus.RUNNING or job.worker_id is None:
            raise IllegalTransition("job is not claimed")
        return ClaimToken(job.job_id, job.worker_id, job.claim_version)

    @staticmethod
    def require_claim(job: IngestionJob, token: ClaimToken) -> None:
        if (
            job.status is not JobStatus.RUNNING
            or job.job_id != token.job_id
            or job.worker_id != token.worker_id
            or job.claim_version != token.claim_version
        ):
            raise IngestionError("JOB_FENCE_CONFLICT", "job claim token is stale")

    def apply_page(
        self,
        job: IngestionJob,
        token: ClaimToken,
        page_digest: str,
        expected_record_ids: frozenset[str],
        outcome: PageOutcome,
    ) -> bool:
        self.require_claim(job, token)
        if not page_digest:
            raise ValueError("page digest is required")
        if page_digest in job.applied_page_digests:
            return False
        if outcome.record_ids != expected_record_ids:
            raise IngestionError("JOB_COUNT_MISMATCH", "page outcomes do not reconcile")
        job.succeeded_count += len(outcome.succeeded)
        job.quarantined_count += len(outcome.quarantined)
        job.failed_count += len(outcome.failed)
        job.durable_cursor = outcome.next_cursor
        job.applied_page_digests.add(page_digest)
        return True

    def crash(self, job: IngestionJob, token: ClaimToken) -> None:
        self.require_claim(job, token)
        job.schedule_retry()

    def finish(self, job: IngestionJob, token: ClaimToken, at: datetime) -> None:
        self.require_claim(job, token)
        job.finish(at)
