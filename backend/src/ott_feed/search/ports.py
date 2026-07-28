"""Framework-free search ports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ott_feed.search.domain.models import SearchCandidate, StructuredQuery


class EmbeddingPort(Protocol):
    def embed(self, text: str) -> Sequence[float]: ...


class TextSearchPort(Protocol):
    def search(self, query: StructuredQuery, limit: int) -> list[SearchCandidate]: ...


class VectorSearchPort(Protocol):
    def search(
        self, vector: Sequence[float], generation: str, limit: int
    ) -> list[SearchCandidate]: ...


class RateLimitPort(Protocol):
    def allow(self, bucket: str, subject: str, cost: int = 1) -> bool: ...


class SearchTelemetryPort(Protocol):
    def result(self, *, degraded_reason: str | None, result_count: int) -> None: ...
