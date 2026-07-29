"""Authenticated U05 recommendation routes."""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Header

from ott_feed.recommendation.api.contracts import (
    RecommendationContract,
    RecommendRequest,
    ResetRequest,
)
from ott_feed.recommendation.domain.errors import invalid, unavailable


class RecommendationFacade(Protocol):
    def recommend(
        self, owner_id: str, request: RecommendRequest, idempotency_key: str
    ) -> RecommendationContract: ...

    def refine(
        self, owner_id: str, session_id: str, request: RecommendRequest, idempotency_key: str
    ) -> RecommendationContract: ...

    def reset(
        self, owner_id: str, session_id: str, request: ResetRequest, idempotency_key: str
    ) -> None: ...


class UnavailableRecommendationFacade:
    def recommend(
        self, owner_id: str, request: RecommendRequest, idempotency_key: str
    ) -> RecommendationContract:
        del owner_id, request, idempotency_key
        raise unavailable("recommendation_unavailable", "recommendation service unavailable")

    def refine(
        self,
        owner_id: str,
        session_id: str,
        request: RecommendRequest,
        idempotency_key: str,
    ) -> RecommendationContract:
        del owner_id, session_id, request, idempotency_key
        raise unavailable("recommendation_unavailable", "recommendation service unavailable")

    def reset(
        self, owner_id: str, session_id: str, request: ResetRequest, idempotency_key: str
    ) -> None:
        del owner_id, session_id, request, idempotency_key
        raise unavailable("recommendation_unavailable", "recommendation service unavailable")


def create_recommendation_router(facade: RecommendationFacade) -> APIRouter:
    router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

    def identity(x_user_id: str | None) -> str:
        if not x_user_id:
            raise invalid("authentication_required", "authentication required")
        return x_user_id

    @router.post("", response_model=RecommendationContract)
    def recommend(
        request: RecommendRequest,
        x_user_id: str | None = Header(default=None),
        idempotency_key: str = Header(min_length=1, max_length=160),
    ) -> RecommendationContract:
        return facade.recommend(identity(x_user_id), request, idempotency_key)

    @router.post("/{session_id}/refine", response_model=RecommendationContract)
    def refine(
        session_id: str,
        request: RecommendRequest,
        x_user_id: str | None = Header(default=None),
        idempotency_key: str = Header(min_length=1, max_length=160),
    ) -> RecommendationContract:
        return facade.refine(identity(x_user_id), session_id, request, idempotency_key)

    @router.post("/{session_id}/reset", status_code=204)
    def reset(
        session_id: str,
        request: ResetRequest,
        x_user_id: str | None = Header(default=None),
        idempotency_key: str = Header(min_length=1, max_length=160),
    ) -> None:
        facade.reset(identity(x_user_id), session_id, request, idempotency_key)

    return router
