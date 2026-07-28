"""Search values shared by parsers and retrieval services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StructuredQuery:
    text: str
    locale: str
    genres: frozenset[str] = frozenset()
    providers: frozenset[str] = frozenset()
    people: tuple[str, ...] = ()
    max_runtime_minutes: int | None = None
    unresolved_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.locale:
            raise ValueError("locale is required")
        if self.max_runtime_minutes is not None and self.max_runtime_minutes <= 0:
            raise ValueError("max runtime must be positive")


@dataclass(frozen=True, slots=True)
class SearchCandidate:
    content_id: str
    score: float
    title: str
    actual_locale: str
    source: str


@dataclass(frozen=True, slots=True)
class RankedResult:
    candidate: SearchCandidate
    rank: int
    channels: tuple[str, ...]
