"""Feed/detail HTTP routes with no-store responses."""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, HTTPException, Query, Response

from ott_feed.catalog.api.contracts import DetailResponse, FeedItemResponse, FeedResponse
from ott_feed.catalog.application.detail import ContentDetail
from ott_feed.catalog.application.feed import FeedPage
from ott_feed.search.adapters.security import CursorSigner


class CatalogFacade(Protocol):
    def feed(self, *, region: str, locale: str, page_size: int, cursor: str | None) -> FeedPage: ...

    def detail(self, content_id: str, *, region: str, locale: str) -> ContentDetail: ...


class UnavailableCatalogFacade:
    def feed(self, *, region: str, locale: str, page_size: int, cursor: str | None) -> FeedPage:
        raise HTTPException(status_code=503, detail="catalog unavailable")

    def detail(self, content_id: str, *, region: str, locale: str) -> ContentDetail:
        raise HTTPException(status_code=503, detail="catalog unavailable")


def create_catalog_router(facade: CatalogFacade, signer: CursorSigner) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["catalog"])

    @router.get("/feed", response_model=FeedResponse)
    def feed(
        response: Response,
        region: str = Query(min_length=2, max_length=8),
        locale: str = Query(default="ko-KR", min_length=2, max_length=20),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=2048),
    ) -> FeedResponse:
        page = facade.feed(region=region, locale=locale, page_size=page_size, cursor=cursor)
        response.headers["Cache-Control"] = "no-store"
        return FeedResponse(
            items=[
                FeedItemResponse.model_validate(item, from_attributes=True) for item in page.items
            ],
            nextCursor=signer.encode(page.next_cursor) if page.next_cursor else None,
            generation=page.generation,
            queryFingerprint=page.fingerprint,
        )

    @router.get("/contents/{content_id}", response_model=DetailResponse)
    def detail(
        content_id: str,
        response: Response,
        region: str = Query(min_length=2, max_length=8),
        locale: str = Query(default="ko-KR", min_length=2, max_length=20),
    ) -> DetailResponse:
        value = facade.detail(content_id, region=region, locale=locale)
        response.headers["Cache-Control"] = "no-store"
        return DetailResponse.model_validate(value, from_attributes=True)

    return router
