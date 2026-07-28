"""U04 six-lane worker registration and budgets."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ott_feed.platform.application.outbox import HandlerRegistry


@dataclass(frozen=True, slots=True)
class U04LaneBudgets:
    withdrawal: int = 1
    publication: int = 1
    incremental: int = 4
    revalidation: int = 1
    full_sync: int = 1
    retention: int = 1

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (
                self.withdrawal,
                self.publication,
                self.incremental,
                self.revalidation,
                self.full_sync,
                self.retention,
            )
        ):
            raise ValueError("U04 lane budgets must be positive")


@dataclass(frozen=True, slots=True)
class IngestionWorkerHandlers:
    withdrawal: Callable[[dict[str, object]], None]
    publication: Callable[[dict[str, object]], None]
    incremental: Callable[[dict[str, object]], None]
    revalidation: Callable[[dict[str, object]], None]
    full_sync: Callable[[dict[str, object]], None]
    retention: Callable[[dict[str, object]], None]


def register_ingestion_handlers(
    registry: HandlerRegistry,
    handlers: IngestionWorkerHandlers,
    budgets: U04LaneBudgets,
) -> None:
    def budgeted(
        handler: Callable[[dict[str, object]], None], budget: int
    ) -> Callable[[dict[str, object]], None]:
        def invoke(payload: dict[str, object]) -> None:
            handler({**payload, "_budget": budget})

        return invoke

    values = (
        ("u04.withdrawal", handlers.withdrawal, budgets.withdrawal),
        ("u04.publication", handlers.publication, budgets.publication),
        ("u04.incremental", handlers.incremental, budgets.incremental),
        ("u04.revalidation", handlers.revalidation, budgets.revalidation),
        ("u04.full_sync", handlers.full_sync, budgets.full_sync),
        ("u04.retention", handlers.retention, budgets.retention),
    )
    for job_type, handler, budget in values:
        registry.register(job_type, budgeted(handler, budget))
