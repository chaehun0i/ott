"""Framework-free catalog ports shared with U04, U05, U06 and U07."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol, TypeVar

from ott_feed.catalog.domain.models import CatalogContent, CatalogVersion, ContentId

T = TypeVar("T")


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new(self) -> str: ...


class CatalogRepository(Protocol):
    def get(self, content_id: ContentId) -> CatalogContent | None: ...

    def save(self, content: CatalogContent, expected_version: CatalogVersion | None) -> None: ...


class ApprovedCatalogReadPort(Protocol):
    def get_approved(self, content_id: ContentId, region: str) -> CatalogContent | None: ...


class ApprovedCatalogWritePort(Protocol):
    def publish(self, content: CatalogContent, decision_id: str) -> CatalogVersion: ...


class OutboxPort(Protocol):
    def enqueue(self, event_type: str, payload: dict[str, object], lane: str) -> None: ...


class GenerationRegistry(Protocol):
    def active(self, projection: str) -> str | None: ...

    def compare_and_swap(self, projection: str, expected: str | None, candidate: str) -> bool: ...


class UnitOfWork(AbstractContextManager["UnitOfWork"], Protocol):
    catalog: CatalogRepository
    outbox: OutboxPort

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class TelemetryPort(Protocol):
    def increment(self, metric: str, attributes: dict[str, str] | None = None) -> None: ...
