"""Record-isolated pipeline closure without external calls in transactions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import (
    DecisionState,
    QuarantineRecord,
    RawMetadataRecord,
    ValidationDecision,
)


class DecisionTransaction(Protocol):
    def persist_raw(self, value: RawMetadataRecord) -> None: ...

    def persist_decision(self, value: ValidationDecision) -> None: ...

    def persist_quarantine(self, value: QuarantineRecord) -> None: ...

    def enqueue_publication(self, decision_id: str, publication_key: str) -> None: ...

    def commit(self) -> None: ...


TransactionFactory = Callable[[], AbstractContextManager[DecisionTransaction]]


@dataclass(frozen=True, slots=True)
class ClosedRecord:
    raw: RawMetadataRecord
    decision: ValidationDecision
    quarantine: QuarantineRecord | None = None


@dataclass(frozen=True, slots=True)
class PagePipelineResult:
    succeeded: tuple[str, ...]
    quarantined: tuple[str, ...]
    failed: tuple[str, ...]


class RecordPipeline:
    def __init__(self, transactions: TransactionFactory) -> None:
        self.transactions = transactions

    def close(self, value: ClosedRecord) -> DecisionState:
        passed = value.decision.state is DecisionState.PASSED_PENDING_PUBLICATION
        failed = value.decision.state is DecisionState.QUARANTINED
        if passed == failed:
            raise ValidationClosureError("decision must close as passed or quarantined")
        if failed != (value.quarantine is not None):
            raise ValidationClosureError("quarantine presence must match failed decision")
        with self.transactions() as transaction:
            transaction.persist_raw(value.raw)
            transaction.persist_decision(value.decision)
            if failed:
                assert value.quarantine is not None
                transaction.persist_quarantine(value.quarantine)
            else:
                assert value.decision.publication_key is not None
                transaction.enqueue_publication(
                    value.decision.decision_id, value.decision.publication_key
                )
            transaction.commit()
        return value.decision.state

    def process_page(
        self,
        record_ids: Sequence[str],
        handler: Callable[[str], ClosedRecord],
    ) -> PagePipelineResult:
        succeeded: list[str] = []
        quarantined: list[str] = []
        failed: list[str] = []
        for record_id in record_ids:
            try:
                state = self.close(handler(record_id))
                target = quarantined if state is DecisionState.QUARANTINED else succeeded
                target.append(record_id)
            except (ValueError, ValidationClosureError):
                failed.append(record_id)
        return PagePipelineResult(tuple(succeeded), tuple(quarantined), tuple(failed))
