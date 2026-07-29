"""Framework-free U05 dependency and persistence ports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...


class IdGenerator(Protocol):
    def new(self) -> str: ...


class ConsentFeaturePort(Protocol):
    def snapshot(self, subject_id: str, request_id: str) -> Mapping[str, object] | None: ...


class ApprovedRecommendationCatalogPort(Protocol):
    def candidates(self, region: str, limit: int) -> Sequence[object]: ...


class ValidationPredicatePort(Protocol):
    def active(self) -> object: ...


class AIProviderPort(Protocol):
    def interpret(self, payload: Mapping[str, object], timeout_ms: int) -> Mapping[str, object]: ...

    def draft(self, payload: Mapping[str, object], timeout_ms: int) -> Mapping[str, object]: ...


class AggregateRepository(Protocol):
    def get(self, key: str) -> object | None: ...

    def save(self, value: object, expected_version: int | None = None) -> None: ...


class TelemetryPort(Protocol):
    def increment(self, metric: str, attributes: Mapping[str, str] | None = None) -> None: ...

    def observe(
        self, metric: str, value: float, attributes: Mapping[str, str] | None = None
    ) -> None: ...


class RecommendationTracePort(Protocol):
    def read(self, trace_id: str) -> Mapping[str, object] | None: ...


class UnitOfWork(Protocol):
    sessions: AggregateRepository
    requests: AggregateRepository
    policies: AggregateRepository
    rankings: AggregateRepository
    validations: AggregateRepository
    traces: AggregateRepository
    usage: AggregateRepository
    retention: AggregateRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> AbstractContextManager[UnitOfWork]: ...
