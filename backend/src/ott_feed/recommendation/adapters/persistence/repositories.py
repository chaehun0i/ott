"""U05 SQLAlchemy repositories with explicit optimistic closure."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ott_feed.recommendation.adapters.persistence.models import (
    AIUsageRow,
    RankingProofRow,
    RecommendationPolicyRow,
    RecommendationRequestRow,
    RecommendationSessionRow,
    RecommendationTraceRow,
    RetentionCheckpointRow,
    ValidationOutcomeRow,
)
from ott_feed.recommendation.domain.errors import invalid


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, session_id: str) -> RecommendationSessionRow | None:
        return self.session.get(RecommendationSessionRow, session_id)

    def save(self, row: RecommendationSessionRow, expected_version: int | None = None) -> None:
        if expected_version is None:
            self.session.add(row)
            return
        statement = (
            update(RecommendationSessionRow)
            .where(
                RecommendationSessionRow.session_id == row.session_id,
                RecommendationSessionRow.version == expected_version,
            )
            .values(
                epoch=row.epoch,
                version=row.version,
                intent=row.intent,
                idempotency_key=row.idempotency_key,
                updated_at=row.updated_at,
            )
        )
        with self.session.no_autoflush:
            result = self.session.connection().execute(statement)
        if result.rowcount != 1:
            raise invalid("session_conflict", "session version conflict")


class RowRepository:
    def __init__(self, session: Session, row_type: type[object]) -> None:
        self.session = session
        self.row_type = row_type

    def get(self, key: str) -> object | None:
        return self.session.get(self.row_type, key)

    def save(self, value: object, expected_version: int | None = None) -> None:
        del expected_version
        self.session.add(value)


class TraceRepository(RowRepository):
    def expired_ids(self, limit: int, now: datetime | None = None) -> tuple[str, ...]:
        at = now or datetime.now(UTC)
        statement = (
            select(RecommendationTraceRow.trace_id)
            .where(RecommendationTraceRow.expires_at <= at)
            .order_by(RecommendationTraceRow.expires_at, RecommendationTraceRow.trace_id)
            .limit(min(limit, 500))
        )
        return tuple(self.session.scalars(statement))

    def delete_ids(self, ids: tuple[str, ...]) -> int:
        if not ids:
            return 0
        result = self.session.connection().execute(
            delete(RecommendationTraceRow).where(RecommendationTraceRow.trace_id.in_(ids))
        )
        return result.rowcount


ROW_TYPES = {
    "requests": RecommendationRequestRow,
    "policies": RecommendationPolicyRow,
    "rankings": RankingProofRow,
    "validations": ValidationOutcomeRow,
    "traces": RecommendationTraceRow,
    "usage": AIUsageRow,
    "retention": RetentionCheckpointRow,
}
