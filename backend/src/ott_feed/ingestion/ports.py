"""Framework-free ports for U04 providers, persistence and unit contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderRecordEnvelope:
    provider_record_id: str
    payload: bytes
    retrieved_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderPage:
    records: tuple[ProviderRecordEnvelope, ...]
    next_cursor: str | None
    request_id: str


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new(self) -> str: ...


class ProviderPort(Protocol):
    def fetch_page(self, cursor: str | None, limit: int) -> ProviderPage: ...


class ProviderAdapterRegistry(Protocol):
    def resolve(self, provider_id: str) -> ProviderPort: ...


class AggregateRepository(Protocol):
    def get(self, key: str) -> object | None: ...

    def save(self, aggregate: object, expected_version: int | None = None) -> None: ...


class JobRepository(AggregateRepository, Protocol):
    def claim(self, worker_id: str, lanes: Sequence[str], lease_seconds: int) -> object | None: ...


class PublicationRepository(AggregateRepository, Protocol):
    def find_by_key(self, publication_key: str) -> object | None: ...


class ApprovedCatalogCommandPort(Protocol):
    def execute(self, command: object) -> int: ...

    def reconcile(self, decision_id: str) -> int | None: ...


class TelemetryPort(Protocol):
    def increment(self, metric: str, attributes: Mapping[str, str] | None = None) -> None: ...

    def observe(
        self, metric: str, value: float, attributes: Mapping[str, str] | None = None
    ) -> None: ...


class UnitOfWork(Protocol):
    jobs: JobRepository
    policies: AggregateRepository
    raw_records: AggregateRepository
    normalized: AggregateRepository
    merges: AggregateRepository
    validations: AggregateRepository
    quarantine: AggregateRepository
    publications: PublicationRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> AbstractContextManager[UnitOfWork]: ...
