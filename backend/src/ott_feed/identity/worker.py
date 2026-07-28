"""U02 worker handler registration with explicit lane concurrency budgets."""

from __future__ import annotations

from dataclasses import dataclass
from threading import BoundedSemaphore

from ott_feed.identity.domain.errors import unavailable
from ott_feed.platform.application.outbox import HandlerRegistry, JobHandler


@dataclass(frozen=True, slots=True)
class IdentityWorkerHandlers:
    feature_explicit_refresh: JobHandler
    feature_implicit_event: JobHandler
    consent_withdrawal_cleanup: JobHandler
    data_rights_deletion: JobHandler
    data_rights_export: JobHandler
    key_rotation: JobHandler


class LaneBudgets:
    def __init__(self, high: int, normal: int, low: int) -> None:
        if min(high, normal, low) < 1:
            raise ValueError("worker lane budgets must be positive")
        self._budgets = {
            "high": BoundedSemaphore(high),
            "normal": BoundedSemaphore(normal),
            "low": BoundedSemaphore(low),
        }

    def wrap(self, lane: str, handler: JobHandler) -> JobHandler:
        budget = self._budgets[lane]

        def bounded(payload: dict[str, object]) -> None:
            if not budget.acquire(blocking=False):
                raise unavailable("worker_lane_saturated", "identity.try_again")
            try:
                handler(payload)
            finally:
                budget.release()

        return bounded


def register_identity_handlers(
    registry: HandlerRegistry,
    handlers: IdentityWorkerHandlers,
    budgets: LaneBudgets,
) -> None:
    registrations: tuple[tuple[str, str, JobHandler], ...] = (
        ("identity.feature.explicit-refresh", "normal", handlers.feature_explicit_refresh),
        ("identity.feature.implicit-event", "normal", handlers.feature_implicit_event),
        (
            "identity.consent.withdrawal-cleanup",
            "high",
            handlers.consent_withdrawal_cleanup,
        ),
        ("identity.data-rights.deletion", "high", handlers.data_rights_deletion),
        ("identity.data-rights.export", "low", handlers.data_rights_export),
        ("identity.key-rotation", "low", handlers.key_rotation),
    )
    for job_type, lane, handler in registrations:
        registry.register(job_type, budgets.wrap(lane, handler))
