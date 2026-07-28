"""Quarantine lifecycle isolated from technical delivery failures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import (
    DecisionState,
    QuarantineRecord,
    ValidationDecision,
)


@dataclass(frozen=True, slots=True)
class QuarantineStatus:
    quarantine_id: str
    decision_id: str
    reason_codes: tuple[str, ...]
    resolution: str
    opened_at: datetime
    resolved_at: datetime | None


class QuarantineService:
    def open(
        self, decision: ValidationDecision, quarantine_id: str, at: datetime
    ) -> QuarantineRecord:
        if decision.state is not DecisionState.QUARANTINED or not decision.reason_codes:
            raise ValidationClosureError("only a failed validation decision can open quarantine")
        return QuarantineRecord(
            quarantine_id,
            decision.decision_id,
            decision.reason_codes,
            at,
        )

    def supersede(
        self,
        quarantine: QuarantineRecord,
        passed_decision: ValidationDecision,
        at: datetime,
    ) -> None:
        if passed_decision.state not in {
            DecisionState.PASSED_PENDING_PUBLICATION,
            DecisionState.PUBLISHED,
        }:
            raise ValidationClosureError("quarantine requires a superseding passed decision")
        quarantine.supersede(passed_decision.decision_id, at)

    @staticmethod
    def status(value: QuarantineRecord) -> QuarantineStatus:
        return QuarantineStatus(
            value.quarantine_id,
            value.decision_id,
            value.reason_codes,
            value.resolution.value,
            value.opened_at,
            value.resolved_at,
        )
