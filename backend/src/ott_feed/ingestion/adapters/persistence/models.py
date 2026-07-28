"""SQLAlchemy rows owned by the u04_ingestion schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.platform.adapters.database import Base

SCHEMA = "u04_ingestion"


class ProviderPolicyRow(Base):
    __tablename__ = "provider_policies"
    __table_args__ = (
        UniqueConstraint("provider_id", "version", name="uq_u04_provider_policy_version"),
        {"schema": SCHEMA},
    )
    policy_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    policy: Mapped[dict[str, Any]] = mapped_column(JSON)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionJobRow(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = {"schema": SCHEMA}
    job_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(80), index=True)
    policy_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.provider_policies.policy_id"), index=True
    )
    lane: Mapped[str] = mapped_column(String(40), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(30), index=True)
    start_cursor: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    durable_cursor: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    claim_version: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionAttemptRow(Base):
    __tablename__ = "ingestion_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "attempt_number", name="uq_u04_job_attempt"),
        {"schema": SCHEMA},
    )
    attempt_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.ingestion_jobs.job_id", ondelete="CASCADE"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    worker_id: Mapped[str] = mapped_column(String(120))
    claim_version: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(40), nullable=True)


class RawMetadataRow(Base):
    __tablename__ = "raw_metadata"
    __table_args__ = (
        UniqueConstraint(
            "provider_id", "provider_record_id", "payload_digest", name="uq_u04_raw_digest"
        ),
        {"schema": SCHEMA},
    )
    raw_record_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.ingestion_jobs.job_id", ondelete="CASCADE"), index=True
    )
    provider_id: Mapped[str] = mapped_column(String(80), index=True)
    provider_record_id: Mapped[str] = mapped_column(String(300))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload_digest: Mapped[str] = mapped_column(String(64))
    payload_body: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    payload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    policy_id: Mapped[str] = mapped_column(String(120))
    tombstone_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)


class NormalizedMetadataRow(Base):
    __tablename__ = "normalized_metadata"
    __table_args__ = (
        UniqueConstraint(
            "raw_record_id", "normalization_version", name="uq_u04_normalized_version"
        ),
        {"schema": SCHEMA},
    )
    normalized_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    raw_record_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.raw_metadata.raw_record_id", ondelete="CASCADE"), index=True
    )
    normalization_version: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IdentityResolutionRow(Base):
    __tablename__ = "identity_resolutions"
    __table_args__ = (
        UniqueConstraint("normalized_id", "policy_version", name="uq_u04_identity_attempt"),
        {"schema": SCHEMA},
    )
    resolution_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    normalized_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.normalized_metadata.normalized_id", ondelete="CASCADE"), index=True
    )
    policy_version: Mapped[str] = mapped_column(String(80))
    decision: Mapped[str] = mapped_column(String(20), index=True)
    selected_content_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)


class MergedMetadataRow(Base):
    __tablename__ = "merged_metadata"
    __table_args__ = (
        UniqueConstraint("canonical_content_id", "input_digest", name="uq_u04_merge_input"),
        {"schema": SCHEMA},
    )
    merged_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    canonical_content_id: Mapped[str] = mapped_column(String(120), index=True)
    merge_policy_version: Mapped[str] = mapped_column(String(80))
    input_digest: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ValidationRuleRow(Base):
    __tablename__ = "validation_rule_versions"
    __table_args__ = {"schema": SCHEMA}
    rule_version: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON)
    compatible_u03_version: Mapped[str] = mapped_column(String(40))
    compatible_u05_version: Mapped[str] = mapped_column(String(40))
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ValidationRunRow(Base):
    __tablename__ = "validation_runs"
    __table_args__ = (
        UniqueConstraint("attempt_key", name="uq_u04_validation_attempt"),
        {"schema": SCHEMA},
    )
    run_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    merged_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.merged_metadata.merged_id", ondelete="CASCADE"), index=True
    )
    rule_version: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.validation_rule_versions.rule_version"), index=True
    )
    attempt_key: Mapped[str] = mapped_column(String(160))
    trigger: Mapped[str] = mapped_column(String(30))
    actor_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    results: Mapped[dict[str, Any]] = mapped_column(JSON)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ValidationDecisionRow(Base):
    __tablename__ = "validation_decisions"
    __table_args__ = {"schema": SCHEMA}
    decision_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.validation_runs.run_id", ondelete="CASCADE"), unique=True
    )
    state: Mapped[str] = mapped_column(String(40), index=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON)
    publication_key: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    catalog_version: Mapped[int | None] = mapped_column(nullable=True, unique=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QuarantineRow(Base):
    __tablename__ = "quarantine_records"
    __table_args__ = {"schema": SCHEMA}
    quarantine_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.validation_decisions.decision_id", ondelete="CASCADE"), unique=True
    )
    reason_codes: Mapped[list[str]] = mapped_column(JSON)
    resolution: Mapped[str] = mapped_column(String(40), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_attempt_id: Mapped[str | None] = mapped_column(String(120), nullable=True)


class PublicationReceiptRow(Base):
    __tablename__ = "publication_receipts"
    __table_args__ = {"schema": SCHEMA}
    publication_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.validation_decisions.decision_id", ondelete="CASCADE"), unique=True
    )
    catalog_version: Mapped[int] = mapped_column(unique=True)
    outcome: Mapped[str] = mapped_column(String(30))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RetentionProgressRow(Base):
    __tablename__ = "retention_progress"
    __table_args__ = {"schema": SCHEMA}
    provider_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    last_raw_record_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
