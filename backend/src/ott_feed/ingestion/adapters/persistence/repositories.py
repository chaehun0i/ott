"""U04 repositories with bounded claims, fencing and typed failures."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast

from sqlalchemy import Select, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ott_feed.ingestion.adapters.persistence.models import (
    IngestionAttemptRow,
    IngestionJobRow,
    MergedMetadataRow,
    NormalizedMetadataRow,
    ProviderPolicyRow,
    PublicationReceiptRow,
    QuarantineRow,
    RawMetadataRow,
    ValidationDecisionRow,
    ValidationRuleRow,
    ValidationRunRow,
)
from ott_feed.ingestion.domain.errors import IngestionError

RowT = TypeVar("RowT")


class RowRepository[RowT]:
    def __init__(self, session: Session, row_type: type[RowT]) -> None:
        self.session = session
        self.row_type = row_type

    def get(self, key: object) -> RowT | None:
        return self.session.get(self.row_type, key)

    def add(self, row: RowT) -> None:
        try:
            self.session.add(row)
            self.session.flush()
        except IntegrityError as exc:
            raise IngestionError("U04_PERSISTENCE_CONFLICT", "duplicate U04 record") from exc


class JobRepository(RowRepository[IngestionJobRow]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, IngestionJobRow)

    def claim(
        self,
        worker_id: str,
        lanes: Sequence[str],
        lease_seconds: int,
        *,
        now: datetime | None = None,
    ) -> IngestionJobRow | None:
        if not lanes or lease_seconds <= 0:
            raise ValueError("claim lanes and lease must be bounded")
        at = now or datetime.now(UTC)
        statement: Select[tuple[IngestionJobRow]] = (
            select(IngestionJobRow)
            .where(
                IngestionJobRow.lane.in_(lanes),
                IngestionJobRow.status.in_(("scheduled", "retry_pending")),
                IngestionJobRow.available_at <= at,
                (IngestionJobRow.lease_until.is_(None) | (IngestionJobRow.lease_until < at)),
            )
            .order_by(
                IngestionJobRow.available_at,
                IngestionJobRow.priority,
                IngestionJobRow.job_id,
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        try:
            row = self.session.scalar(statement)
            if row is None:
                return None
            row.status = "running"
            row.lease_owner = worker_id
            row.lease_until = at + timedelta(seconds=lease_seconds)
            row.claim_version += 1
            self.session.add(
                IngestionAttemptRow(
                    attempt_id=f"{row.job_id}:{row.claim_version}",
                    job_id=row.job_id,
                    attempt_number=row.claim_version,
                    worker_id=worker_id,
                    claim_version=row.claim_version,
                    started_at=at,
                )
            )
            self.session.flush()
            return row
        except OperationalError as exc:
            raise IngestionError(
                "U04_PERSISTENCE_UNAVAILABLE", "job claim store unavailable", retryable=True
            ) from exc

    def advance_cursor(
        self,
        job_id: str,
        expected_claim_version: int,
        cursor: str | None,
        summary: dict[str, Any],
    ) -> None:
        result = cast(
            CursorResult[Any],
            self.session.execute(
                update(IngestionJobRow)
                .where(
                    IngestionJobRow.job_id == job_id,
                    IngestionJobRow.claim_version == expected_claim_version,
                    IngestionJobRow.status == "running",
                )
                .values(durable_cursor=cursor, summary=summary)
            ),
        )
        if result.rowcount != 1:
            raise IngestionError("JOB_FENCE_CONFLICT", "job claim is no longer current")


class RawRecordRepository(RowRepository[RawMetadataRow]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, RawMetadataRow)

    def find_observation(
        self, provider_id: str, provider_record_id: str, payload_digest: str
    ) -> RawMetadataRow | None:
        return self.session.scalar(
            select(RawMetadataRow).where(
                RawMetadataRow.provider_id == provider_id,
                RawMetadataRow.provider_record_id == provider_record_id,
                RawMetadataRow.payload_digest == payload_digest,
            )
        )

    def expire_batch(self, at: datetime, limit: int) -> tuple[str, ...]:
        if limit <= 0:
            raise ValueError("retention batch must be positive")
        rows = self.session.scalars(
            select(RawMetadataRow)
            .where(
                RawMetadataRow.payload_body.is_not(None), RawMetadataRow.payload_expires_at <= at
            )
            .order_by(RawMetadataRow.payload_expires_at, RawMetadataRow.raw_record_id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).all()
        for row in rows:
            row.payload_body = None
        self.session.flush()
        return tuple(row.raw_record_id for row in rows)


class IngestionRepositories:
    def __init__(self, session: Session) -> None:
        self.jobs = JobRepository(session)
        self.policies = RowRepository(session, ProviderPolicyRow)
        self.raw_records = RawRecordRepository(session)
        self.normalized = RowRepository(session, NormalizedMetadataRow)
        self.merges = RowRepository(session, MergedMetadataRow)
        self.rules = RowRepository(session, ValidationRuleRow)
        self.validation_runs = RowRepository(session, ValidationRunRow)
        self.validations = RowRepository(session, ValidationDecisionRow)
        self.quarantine = RowRepository(session, QuarantineRow)
        self.publications = RowRepository(session, PublicationReceiptRow)
