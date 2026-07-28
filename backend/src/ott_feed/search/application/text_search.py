"""Approved text-search orchestration with deterministic closure filtering."""

from __future__ import annotations

from datetime import datetime

from ott_feed.catalog.application.closure import ApprovedClosureGuard
from ott_feed.catalog.domain.errors import CatalogError
from ott_feed.search.domain.models import SearchCandidate, StructuredQuery
from ott_feed.search.ports import TextSearchPort


class TextSearchService:
    def __init__(self, repository: TextSearchPort, closure: ApprovedClosureGuard) -> None:
        self.repository = repository
        self.closure = closure

    def search(
        self, query: StructuredQuery, *, region: str, now: datetime, limit: int = 20
    ) -> list[SearchCandidate]:
        if not region or not 1 <= limit <= 50:
            raise ValueError("region and a limit within 1..50 are required")
        result: list[SearchCandidate] = []
        for candidate in self.repository.search(query, limit * 2):
            try:
                self.closure.require(candidate.content_id, region, now)
            except CatalogError:
                continue
            result.append(candidate)
            if len(result) == limit:
                break
        return result
