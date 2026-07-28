"""Natural-language discovery route with cost-aware rate limiting."""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Header, HTTPException, Response

from ott_feed.search.api.contracts import SearchItemResponse, SearchRequest, SearchResponse
from ott_feed.search.domain.models import RankedResult
from ott_feed.search.ports import RateLimitPort


class SearchFacade(Protocol):
    def search(self, request: SearchRequest) -> tuple[list[RankedResult], str | None, str]: ...


class UnavailableSearchFacade:
    def search(self, request: SearchRequest) -> tuple[list[RankedResult], str | None, str]:
        raise HTTPException(status_code=503, detail="search unavailable")


def create_search_router(facade: SearchFacade, rate_limit: RateLimitPort) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["search"])

    @router.post("/search", response_model=SearchResponse)
    def search(
        request: SearchRequest,
        response: Response,
        authorization: str | None = Header(default=None),
    ) -> SearchResponse:
        subject = authorization or "anonymous"
        bucket = "semantic_authenticated" if authorization else "semantic_anonymous"
        if not rate_limit.allow(bucket, subject, cost=3):
            raise HTTPException(status_code=429, detail="search rate limit exceeded")
        results, degraded_reason, generation = facade.search(request)
        response.headers["Cache-Control"] = "no-store"
        return SearchResponse(
            items=[
                SearchItemResponse(
                    contentId=item.candidate.content_id,
                    title=item.candidate.title,
                    actualLocale=item.candidate.actual_locale,
                    rank=item.rank,
                    channels=list(item.channels),
                )
                for item in results
            ],
            degradedReason=degraded_reason,
            generation=generation,
        )

    return router
