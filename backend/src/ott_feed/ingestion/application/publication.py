"""Idempotent U03 publication dispatch and unknown-outcome reconciliation."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ott_feed.ingestion.contracts import ApprovedCatalogCommand, ApprovedCatalogCommandMapper
from ott_feed.ingestion.domain.errors import IngestionError
from ott_feed.ingestion.domain.models import (
    PublicationOutcome,
    PublicationReceipt,
    ValidationDecision,
)


class CatalogPublicationPort(Protocol):
    def execute(self, command: ApprovedCatalogCommand) -> int: ...

    def reconcile(self, decision_id: str) -> int | None: ...


class PublicationReceiptStore(Protocol):
    def get(self, publication_key: str) -> PublicationReceipt | None: ...

    def save(self, receipt: PublicationReceipt) -> None: ...


class DecisionAcknowledgementPort(Protocol):
    def acknowledge(self, decision_id: str, catalog_version: int, at: datetime) -> None: ...


class PublicationDispatcher:
    def __init__(
        self,
        catalog: CatalogPublicationPort,
        receipts: PublicationReceiptStore,
        decisions: DecisionAcknowledgementPort,
    ) -> None:
        self.catalog = catalog
        self.receipts = receipts
        self.decisions = decisions
        self.mapper = ApprovedCatalogCommandMapper()

    def dispatch(
        self, decision: ValidationDecision, at: datetime, *, action: str = "publish"
    ) -> PublicationReceipt:
        command = self.mapper.map(decision, action=action)
        existing = self.receipts.get(command.publication_key)
        if existing is not None:
            return existing
        outcome = (
            PublicationOutcome.WITHDRAWN if action == "withdraw" else PublicationOutcome.PUBLISHED
        )
        try:
            catalog_version = self.catalog.execute(command)
        except TimeoutError as exc:
            reconciled_version = self.catalog.reconcile(command.decision_id)
            if reconciled_version is None:
                raise IngestionError(
                    "U03_PUBLICATION_UNKNOWN",
                    "U03 publication outcome is unknown; retry the same key",
                    retryable=True,
                ) from exc
            catalog_version = reconciled_version
            outcome = PublicationOutcome.ALREADY_APPLIED
        receipt = PublicationReceipt(
            command.publication_key,
            command.decision_id,
            catalog_version,
            outcome,
            at,
        )
        self.receipts.save(receipt)
        self.decisions.acknowledge(command.decision_id, catalog_version, at)
        return receipt
