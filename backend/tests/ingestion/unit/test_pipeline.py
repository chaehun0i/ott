from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from types import TracebackType

import pytest

from ott_feed.ingestion.application.pipeline import ClosedRecord, RecordPipeline
from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import (
    DecisionState,
    QuarantineRecord,
    RawMetadataRecord,
    ValidationDecision,
)

NOW = datetime(2026, 7, 28, tzinfo=UTC)


class FakeTransaction(AbstractContextManager["FakeTransaction"]):
    def __init__(self) -> None:
        self.events: list[str] = []

    def __enter__(self) -> FakeTransaction:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def persist_raw(self, _: RawMetadataRecord) -> None:
        self.events.append("raw")

    def persist_decision(self, _: ValidationDecision) -> None:
        self.events.append("decision")

    def persist_quarantine(self, _: QuarantineRecord) -> None:
        self.events.append("quarantine")

    def enqueue_publication(self, _: str, __: str) -> None:
        self.events.append("publication")

    def commit(self) -> None:
        self.events.append("commit")


def raw(record_id: str) -> RawMetadataRecord:
    return RawMetadataRecord(
        record_id,
        "job",
        "provider",
        record_id,
        NOW,
        "a" * 64,
        b"{}",
        "policy",
        NOW + timedelta(days=1),
    )


def closed(record_id: str, passed: bool) -> ClosedRecord:
    decision = ValidationDecision(
        f"d-{record_id}",
        f"r-{record_id}",
        f"m-{record_id}",
        "rules",
        DecisionState.PASSED_PENDING_PUBLICATION if passed else DecisionState.QUARANTINED,
        reason_codes=() if passed else ("VAL_FAILED",),
        publication_key=f"key-{record_id}" if passed else None,
    )
    quarantine = (
        None
        if passed
        else QuarantineRecord(f"q-{record_id}", decision.decision_id, decision.reason_codes, NOW)
    )
    return ClosedRecord(raw(record_id), decision, quarantine)


def test_pass_and_failure_close_to_exactly_one_side_effect() -> None:
    transactions: list[FakeTransaction] = []

    def factory() -> FakeTransaction:
        value = FakeTransaction()
        transactions.append(value)
        return value

    pipeline = RecordPipeline(factory)
    pipeline.close(closed("passed", True))
    pipeline.close(closed("failed", False))
    assert transactions[0].events == ["raw", "decision", "publication", "commit"]
    assert transactions[1].events == ["raw", "decision", "quarantine", "commit"]


def test_malformed_sibling_does_not_block_other_records() -> None:
    pipeline = RecordPipeline(FakeTransaction)

    def handler(record_id: str) -> ClosedRecord:
        if record_id == "bad":
            raise ValueError("malformed")
        return closed(record_id, record_id != "quarantine")

    result = pipeline.process_page(("good", "bad", "quarantine"), handler)
    assert result.succeeded == ("good",)
    assert result.failed == ("bad",)
    assert result.quarantined == ("quarantine",)


def test_incomplete_decision_closure_fails_before_transaction() -> None:
    pipeline = RecordPipeline(FakeTransaction)
    invalid = ClosedRecord(
        raw("x"), closed("x", True).decision, QuarantineRecord("q", "d", ("x",), NOW)
    )
    with pytest.raises(ValidationClosureError):
        pipeline.close(invalid)
