"""SQLAlchemy persistence for U07 runtime records."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from ott_feed.platform.domain.models import JobStatus, OutboxJob, utc_now


class Base(DeclarativeBase):
    pass


class OutboxJobRow(Base):
    __tablename__ = "outbox_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    lane: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(30), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    previous_job_id: Mapped[UUID | None] = mapped_column(nullable=True)


class IdempotencyRow(Base):
    __tablename__ = "idempotency_records"
    scope: Mapped[str] = mapped_column(String(100), primary_key=True)
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), index=True)
    response_status: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ReleaseArtifactRow(Base):
    __tablename__ = "release_artifacts"
    release_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    git_revision: Mapped[str] = mapped_column(String(64), index=True)
    release_tag: Mapped[str] = mapped_column(String(100), unique=True)
    image_digest: Mapped[str] = mapped_column(String(100), unique=True)
    contract_major: Mapped[int] = mapped_column(Integer)
    contract_fingerprint: Mapped[str] = mapped_column(String(64))
    migration_compatible: Mapped[bool] = mapped_column(Boolean)


class DeploymentRecordRow(Base):
    __tablename__ = "deployment_records"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    release_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    previous_digest: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BackupRecordRow(Base):
    __tablename__ = "backup_records"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)


class RestoreAttemptRow(Base):
    __tablename__ = "restore_attempts"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    backup_id: Mapped[UUID] = mapped_column(index=True)
    previous_attempt_id: Mapped[UUID | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    integrity_ok: Mapped[bool] = mapped_column(Boolean)
    smoke_ok: Mapped[bool] = mapped_column(Boolean)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)


def create_database_engine(url: str, pool_size: int, statement_timeout_ms: int = 3000) -> Engine:
    engine = create_engine(url, pool_size=pool_size, max_overflow=0, pool_pre_ping=True)
    if url.startswith("postgresql"):
        with engine.begin() as connection:
            connection.execute(text(f"SET statement_timeout = {int(statement_timeout_ms)}"))
    return engine


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def _to_domain(row: OutboxJobRow) -> OutboxJob:
    available_at = (
        row.available_at if row.available_at.tzinfo else row.available_at.replace(tzinfo=UTC)
    )
    lease_until = row.lease_until
    if lease_until is not None and lease_until.tzinfo is None:
        lease_until = lease_until.replace(tzinfo=UTC)
    return OutboxJob(
        id=row.id,
        job_type=row.job_type,
        payload=row.payload,
        lane=row.lane,
        priority=row.priority,
        status=JobStatus(row.status),
        attempt_count=row.attempt_count,
        max_attempts=row.max_attempts,
        lease_owner=row.lease_owner,
        lease_until=lease_until,
        available_at=available_at,
        failure_code=row.failure_code,
        previous_job_id=row.previous_job_id,
    )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(self, job: OutboxJob) -> None:
        self.session.add(
            OutboxJobRow(
                id=job.id,
                job_type=job.job_type,
                payload=job.payload,
                lane=job.lane,
                priority=job.priority,
                status=job.status.value,
                attempt_count=job.attempt_count,
                max_attempts=job.max_attempts,
                available_at=job.available_at,
                previous_job_id=job.previous_job_id,
            )
        )

    def claim(
        self, worker_id: str, job_types: tuple[str, ...], lease_for: timedelta
    ) -> OutboxJob | None:
        now = utc_now()
        stmt = (
            select(OutboxJobRow)
            .where(
                OutboxJobRow.job_type.in_(job_types),
                OutboxJobRow.available_at <= now,
                (OutboxJobRow.status.in_([JobStatus.PENDING.value, JobStatus.RETRY_WAIT.value]))
                | (
                    (OutboxJobRow.status == JobStatus.PROCESSING.value)
                    & (OutboxJobRow.lease_until <= now)
                ),
            )
            .order_by(
                OutboxJobRow.lane,
                OutboxJobRow.priority,
                OutboxJobRow.available_at,
                OutboxJobRow.id,
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        job = _to_domain(row)
        job.claim(worker_id, lease_for, now)
        self.save(job)
        return job

    def save(self, job: OutboxJob) -> None:
        row = self.session.get(OutboxJobRow, job.id)
        if row is None:
            raise KeyError(job.id)
        row.status = job.status.value
        row.attempt_count = job.attempt_count
        row.lease_owner = job.lease_owner
        row.lease_until = job.lease_until
        row.available_at = job.available_at
        row.failure_code = job.failure_code
        row.lane = job.lane
        row.priority = job.priority
