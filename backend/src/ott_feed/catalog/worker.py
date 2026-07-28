"""Ordered incremental projection handler and gap barrier."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import BoundedSemaphore
from uuid import UUID

from ott_feed.catalog.domain.errors import ProjectionGapError
from ott_feed.platform.application.outbox import HandlerRegistry, JobHandler
from ott_feed.search.adapters.persistence.repositories import SqlAlchemyProjectionRepository


@dataclass(frozen=True, slots=True)
class ProjectionEvent:
    event_id: UUID
    content_id: str
    catalog_version: int


class IncrementalProjectionHandler:
    def __init__(
        self,
        repository: SqlAlchemyProjectionRepository,
        projection: str,
        apply: Callable[[ProjectionEvent], None],
        replay: Callable[[int], None],
    ) -> None:
        self.repository = repository
        self.projection = projection
        self.apply = apply
        self.replay = replay

    def __call__(self, event: ProjectionEvent) -> None:
        if self.repository.has_receipt(event.event_id, self.projection):
            return
        current = self.repository.contiguous_version(self.projection)
        expected = current + 1
        if event.catalog_version != expected:
            if event.catalog_version > expected:
                self.repository.record_gap(self.projection, expected)
                self.replay(expected)
                raise ProjectionGapError()
            return
        self.apply(event)
        if not self.repository.advance(self.projection, current, event.catalog_version):
            raise ProjectionGapError()
        self.repository.receipt(
            event.event_id, self.projection, event.content_id, event.catalog_version
        )


@dataclass(frozen=True, slots=True)
class CatalogWorkerHandlers:
    incremental_feed: JobHandler
    replay_gap: JobHandler


class U03LaneBudgets:
    def __init__(self, incremental: int = 2, embedding: int = 4, rebuild: int = 1) -> None:
        if min(incremental, embedding, rebuild) < 1:
            raise ValueError("U03 worker budgets must be positive")
        self._budgets = {
            "incremental": BoundedSemaphore(incremental),
            "embedding": BoundedSemaphore(embedding),
            "rebuild": BoundedSemaphore(rebuild),
        }

    def wrap(self, lane: str, handler: JobHandler) -> JobHandler:
        semaphore = self._budgets[lane]

        def bounded(payload: dict[str, object]) -> None:
            if not semaphore.acquire(blocking=False):
                raise RuntimeError("u03 worker lane saturated")
            try:
                handler(payload)
            finally:
                semaphore.release()

        return bounded


def register_catalog_handlers(
    registry: HandlerRegistry,
    handlers: CatalogWorkerHandlers,
    budgets: U03LaneBudgets,
) -> None:
    registry.register(
        "u03.projection.incremental-feed",
        budgets.wrap("incremental", handlers.incremental_feed),
    )
    registry.register("u03.projection.replay-gap", budgets.wrap("incremental", handlers.replay_gap))
