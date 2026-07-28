"""Composition adapter from the U04 command port to the U03 publication service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from ott_feed.catalog.application.commands import PassedValidationCommand, PublicationAction
from ott_feed.catalog.domain.models import CatalogContent, CatalogVersion
from ott_feed.ingestion.contracts import ApprovedCatalogCommand


class U03PublicationService(Protocol):
    def execute(self, command: PassedValidationCommand) -> CatalogVersion: ...


class U03CatalogPublicationAdapter:
    def __init__(
        self,
        service: U03PublicationService,
        content_resolver: Callable[[str], CatalogContent | None],
        receipt_lookup: Callable[[str], int | None],
    ) -> None:
        self.service = service
        self.content_resolver = content_resolver
        self.receipt_lookup = receipt_lookup

    def execute(self, command: ApprovedCatalogCommand) -> int:
        action = PublicationAction(command.action)
        content = (
            self.content_resolver(command.merged_id)
            if action in {PublicationAction.PUBLISH, PublicationAction.REPLACE}
            else None
        )
        if content is None and action in {PublicationAction.PUBLISH, PublicationAction.REPLACE}:
            raise ValueError("approved catalog content projection is unavailable")
        u03_command = PassedValidationCommand(
            action,
            content.id if content is not None else command.merged_id,
            command.decision_id,
            content,
        )
        return self.service.execute(u03_command).value

    def reconcile(self, decision_id: str) -> int | None:
        return self.receipt_lookup(decision_id)
