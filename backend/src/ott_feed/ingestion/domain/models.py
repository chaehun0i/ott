"""Framework-free U04 domain values and aggregate state machines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from ott_feed.ingestion.domain.errors import IllegalTransition, ValidationClosureError


class ProviderPolicyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class JobStatus(StrEnum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    RETRY_PENDING = "retry_pending"
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IdentityDecision(StrEnum):
    NEW = "new"
    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"


class RuleOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"


class DecisionState(StrEnum):
    QUARANTINED = "quarantined"
    PASSED_PENDING_PUBLICATION = "passed_pending_publication"
    PUBLISHED = "published"
    WITHDRAWAL_PENDING = "withdrawal_pending"
    WITHDRAWN = "withdrawn"


class QuarantineResolution(StrEnum):
    UNRESOLVED = "unresolved"
    SUPERSEDED_BY_PASS = "superseded_by_pass"
    PERMANENTLY_REJECTED = "permanently_rejected"


class TombstoneKind(StrEnum):
    CONTENT = "content"
    AVAILABILITY = "availability"


class PublicationOutcome(StrEnum):
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"
    ALREADY_APPLIED = "already_applied"


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    policy_id: str
    provider_id: str
    version: int
    status: ProviderPolicyStatus
    allowed_uses: frozenset[str]
    regions: frozenset[str]
    retention_seconds: int
    refresh_seconds: int
    effective_from: datetime
    effective_until: datetime | None = None
    attribution: str = ""

    def __post_init__(self) -> None:
        if not self.policy_id or not self.provider_id or self.version <= 0:
            raise ValueError("policy identity and version are required")
        if self.retention_seconds <= 0 or self.refresh_seconds <= 0:
            raise ValueError("retention and refresh windows must be positive")
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("policy effective window is invalid")

    def active_at(self, at: datetime) -> bool:
        return (
            self.status is ProviderPolicyStatus.ACTIVE
            and at >= self.effective_from
            and (self.effective_until is None or at < self.effective_until)
        )


@dataclass(slots=True)
class IngestionJob:
    job_id: str
    provider_id: str
    policy_id: str
    start_cursor: str | None
    durable_cursor: str | None = None
    status: JobStatus = JobStatus.SCHEDULED
    claim_version: int = 0
    worker_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    succeeded_count: int = 0
    quarantined_count: int = 0
    failed_count: int = 0
    applied_page_digests: set[str] = field(default_factory=set)

    def claim(self, worker_id: str, at: datetime) -> int:
        if self.status not in {JobStatus.SCHEDULED, JobStatus.RETRY_PENDING}:
            raise IllegalTransition(f"cannot claim job in {self.status}")
        if not worker_id:
            raise ValueError("worker ID is required")
        self.status = JobStatus.RUNNING
        self.worker_id = worker_id
        self.started_at = self.started_at or at
        self.claim_version += 1
        return self.claim_version

    def schedule_retry(self) -> None:
        if self.status is not JobStatus.RUNNING:
            raise IllegalTransition("only a running job can retry")
        self.status = JobStatus.RETRY_PENDING
        self.worker_id = None

    def finish(self, at: datetime) -> None:
        if self.status is not JobStatus.RUNNING:
            raise IllegalTransition("only a running job can finish")
        total = self.succeeded_count + self.quarantined_count + self.failed_count
        if total == 0 or self.failed_count > 0:
            self.status = JobStatus.FAILED
        elif self.quarantined_count > 0:
            self.status = JobStatus.PARTIALLY_SUCCEEDED
        else:
            self.status = JobStatus.SUCCEEDED
        self.finished_at = at
        self.worker_id = None


@dataclass(frozen=True, slots=True)
class RawMetadataRecord:
    raw_record_id: str
    job_id: str
    provider_id: str
    provider_record_id: str
    retrieved_at: datetime
    payload_digest: str
    payload_body: bytes | None
    policy_id: str
    payload_expires_at: datetime
    tombstone_kind: TombstoneKind | None = None


@dataclass(frozen=True, slots=True)
class NormalizedMetadata:
    normalized_id: str
    raw_record_id: str
    normalization_version: str
    content_type: str
    identifiers: tuple[tuple[str, str], ...]
    localized_titles: tuple[tuple[str, str], ...]
    runtime_minutes: int | None
    genres: tuple[str, ...]
    source_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalIdentityCandidate:
    resolution_id: str
    normalized_id: str
    policy_version: str
    decision: IdentityDecision
    candidate_content_ids: tuple[str, ...]
    selected_content_id: str | None
    decisive_tier: str | None

    def __post_init__(self) -> None:
        selected = self.selected_content_id is not None
        if self.decision is IdentityDecision.AMBIGUOUS and selected:
            raise ValueError("ambiguous identity cannot select content")
        if self.decision in {IdentityDecision.NEW, IdentityDecision.MATCHED} and not selected:
            raise ValueError("resolved identity requires selected content")


@dataclass(frozen=True, slots=True)
class SourceFieldCandidate:
    path: str
    value: str
    provider_id: str
    normalized_id: str
    observed_at: datetime
    authority: int


@dataclass(frozen=True, slots=True)
class MergedMetadata:
    merged_id: str
    canonical_content_id: str
    merge_policy_version: str
    input_normalized_ids: tuple[str, ...]
    selected_fields: tuple[SourceFieldCandidate, ...]
    alternative_fields: tuple[SourceFieldCandidate, ...]
    computed_at: datetime

    def __post_init__(self) -> None:
        paths = [candidate.path for candidate in self.selected_fields]
        if len(paths) != len(set(paths)):
            raise ValueError("each merged path must have one selected value")


@dataclass(frozen=True, slots=True)
class ValidationRuleVersion:
    version: str
    mandatory_rule_ids: tuple[str, ...]
    compatible_u03_version: str
    compatible_u05_version: str
    effective_from: datetime

    def __post_init__(self) -> None:
        if not self.version or not self.mandatory_rule_ids:
            raise ValueError("validation rule version and mandatory rules are required")
        if len(self.mandatory_rule_ids) != len(set(self.mandatory_rule_ids)):
            raise ValueError("validation rule IDs must be unique")


@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    outcome: RuleOutcome
    reason_code: str | None = None


@dataclass(slots=True)
class ValidationDecision:
    decision_id: str
    run_id: str
    merged_id: str
    rule_version: str
    state: DecisionState
    reason_codes: tuple[str, ...] = ()
    publication_key: str | None = None
    catalog_version: int | None = None
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.state is DecisionState.QUARANTINED and not self.reason_codes:
            raise ValidationClosureError("quarantine requires stable reason codes")
        if self.state is DecisionState.PASSED_PENDING_PUBLICATION and not self.publication_key:
            raise ValidationClosureError("passed decision requires a publication key")

    def acknowledge(self, catalog_version: int, at: datetime) -> None:
        if self.state not in {
            DecisionState.PASSED_PENDING_PUBLICATION,
            DecisionState.WITHDRAWAL_PENDING,
        }:
            raise IllegalTransition("decision is not awaiting publication")
        if catalog_version <= 0:
            raise ValueError("catalog version must be positive")
        self.state = (
            DecisionState.PUBLISHED
            if self.state is DecisionState.PASSED_PENDING_PUBLICATION
            else DecisionState.WITHDRAWN
        )
        self.catalog_version = catalog_version
        self.published_at = at


@dataclass(slots=True)
class QuarantineRecord:
    quarantine_id: str
    decision_id: str
    reason_codes: tuple[str, ...]
    opened_at: datetime
    resolution: QuarantineResolution = QuarantineResolution.UNRESOLVED
    resolved_at: datetime | None = None
    attempt_ids: list[str] = field(default_factory=list)

    def supersede(self, passed_decision_id: str, at: datetime) -> None:
        if self.resolution is not QuarantineResolution.UNRESOLVED:
            raise IllegalTransition("quarantine is already resolved")
        if not passed_decision_id:
            raise ValueError("passed decision ID is required")
        self.resolution = QuarantineResolution.SUPERSEDED_BY_PASS
        self.resolved_at = at


@dataclass(frozen=True, slots=True)
class ProviderTombstone:
    tombstone_id: str
    raw_record_id: str
    provider_id: str
    canonical_content_id: str
    kind: TombstoneKind
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    publication_key: str
    decision_id: str
    catalog_version: int
    outcome: PublicationOutcome
    received_at: datetime

    def __post_init__(self) -> None:
        if self.catalog_version <= 0:
            raise ValueError("catalog version must be positive")
