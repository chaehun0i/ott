"""U06 SQLAlchemy persistence rows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.platform.adapters.database import Base

SCHEMA = "u06_engagement"


class NotificationJobRow(Base):
    __tablename__ = "notification_jobs"
    __table_args__ = (
        UniqueConstraint("deduplication_key", name="uq_u06_job_dedup"),
        Index("ix_u06_job_claim", "channel", "status", "available_at", "job_id"),
        {"schema": SCHEMA},
    )
    job_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    deduplication_key: Mapped[str] = mapped_column(String(64), nullable=False)
    event_id: Mapped[str] = mapped_column(String(120), nullable=False)
    member_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fencing_token: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(100))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OverrideOperationRow(Base):
    __tablename__ = "override_operations"
    __table_args__ = (
        UniqueConstraint("actor_ref", "idempotency_key", name="uq_u06_override_idempotency"),
        {"schema": SCHEMA},
    )
    operation_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    content_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_version: Mapped[int] = mapped_column(Integer, nullable=False)
    patch: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    receipt: Mapped[dict[str, object] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_u06_audit_time", "occurred_at", "audit_id"),
        {"schema": SCHEMA},
    )
    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    canonical_event: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    key_id: Mapped[str] = mapped_column(String(80), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)


class IncidentRow(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index(
            "uq_u06_incident_open_correlation",
            "correlation_key",
            unique=True,
            postgresql_where="state <> 'resolved'",
        ),
        {"schema": SCHEMA},
    )
    incident_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    correlation_key: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120))
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetentionCheckpointRow(Base):
    __tablename__ = "retention_checkpoints"
    __table_args__ = ({"schema": SCHEMA},)
    retention_class: Mapped[str] = mapped_column(String(40), primary_key=True)
    cursor: Mapped[str | None] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
