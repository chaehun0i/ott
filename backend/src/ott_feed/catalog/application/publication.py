"""Atomic approved publication, immutable revision and versioned outbox service."""

from __future__ import annotations

from collections.abc import Callable

from ott_feed.catalog.adapters.persistence.unit_of_work import SqlAlchemyCatalogUnitOfWork
from ott_feed.catalog.application.commands import PassedValidationCommand, PublicationAction
from ott_feed.catalog.domain.errors import ApprovalClosureError, CatalogConflict
from ott_feed.catalog.domain.models import CatalogContent, CatalogState, CatalogVersion
from ott_feed.platform.domain.models import OutboxJob


class ApprovedCatalogPublicationService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyCatalogUnitOfWork]) -> None:
        self.uow_factory = uow_factory

    def execute(self, command: PassedValidationCommand) -> CatalogVersion:
        with self.uow_factory() as uow:
            current = uow.catalog.get(command.content_id)
            if current is not None and current.last_decision_id == command.decision_id:
                return current.version
            expected = current.version if current else None
            result = self._transition(current, command)
            uow.catalog.save(result, expected)
            uow.outbox.enqueue(
                OutboxJob(
                    "u03.catalog.versioned",
                    {
                        "content_id": result.id,
                        "catalog_version": result.version.value,
                        "revision": result.revision,
                        "state": result.state.value,
                        "decision_id": command.decision_id,
                    },
                    lane="high" if result.state is CatalogState.WITHDRAWN else "normal",
                    priority=10 if result.state is CatalogState.WITHDRAWN else 100,
                )
            )
            uow.commit()
            return result.version

    @staticmethod
    def _transition(
        current: CatalogContent | None, command: PassedValidationCommand
    ) -> CatalogContent:
        if command.action is PublicationAction.PUBLISH:
            if current is not None or command.content is None:
                raise CatalogConflict("publish requires a new approved content ID")
            command.content.last_decision_id = command.decision_id
            return command.content
        if current is None:
            raise ApprovalClosureError("CAT_NOT_FOUND")
        if command.action is PublicationAction.REPLACE:
            if command.content is None:
                raise CatalogConflict("replacement content is required")
            return current.replaced(command.content, command.decision_id)
        if command.action is PublicationAction.WITHDRAW:
            current.withdraw(command.decision_id)
            return current
        if command.action is PublicationAction.REACTIVATE:
            current.reactivate(command.decision_id)
            return current
        raise CatalogConflict("unsupported publication action")
