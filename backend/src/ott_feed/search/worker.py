"""Search embedding and online rebuild handler registration."""

from __future__ import annotations

from dataclasses import dataclass

from ott_feed.catalog.worker import U03LaneBudgets
from ott_feed.platform.application.outbox import HandlerRegistry, JobHandler


@dataclass(frozen=True, slots=True)
class SearchWorkerHandlers:
    incremental_text: JobHandler
    embedding: JobHandler
    rebuild: JobHandler


def register_search_handlers(
    registry: HandlerRegistry,
    handlers: SearchWorkerHandlers,
    budgets: U03LaneBudgets,
) -> None:
    registry.register(
        "u03.projection.incremental-text",
        budgets.wrap("incremental", handlers.incremental_text),
    )
    registry.register("u03.embedding.generate", budgets.wrap("embedding", handlers.embedding))
    registry.register("u03.projection.rebuild", budgets.wrap("rebuild", handlers.rebuild))
