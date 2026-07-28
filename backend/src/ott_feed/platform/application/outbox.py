"""Typed worker handler registry and lease-safe dispatcher."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Protocol

from ott_feed.platform.domain.models import OutboxJob, utc_now


class OutboxRepository(Protocol):
    def claim(
        self, worker_id: str, job_types: tuple[str, ...], lease_for: timedelta
    ) -> OutboxJob | None: ...

    def save(self, job: OutboxJob) -> None: ...


JobHandler = Callable[[dict[str, object]], None]


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_type: str, handler: JobHandler) -> None:
        if job_type in self._handlers:
            raise ValueError(f"handler already registered: {job_type}")
        self._handlers[job_type] = handler

    @property
    def job_types(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def handle(self, job: OutboxJob) -> None:
        self._handlers[job.job_type](job.payload)


class WorkerDispatcher:
    def __init__(
        self, worker_id: str, repository: OutboxRepository, registry: HandlerRegistry
    ) -> None:
        self.worker_id = worker_id
        self.repository = repository
        self.registry = registry

    def run_once(self) -> bool:
        job = self.repository.claim(self.worker_id, self.registry.job_types, timedelta(seconds=30))
        if job is None:
            return False
        try:
            self.registry.handle(job)
            job.complete(self.worker_id)
        except Exception as exc:
            retry_at = utc_now() + timedelta(seconds=min(300, 2**job.attempt_count))
            job.fail(self.worker_id, type(exc).__name__, retry_at)
        self.repository.save(job)
        return True
