"""U06 FastAPI router with non-enumerating privileged boundaries."""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends, Header, HTTPException, status

from ott_feed.engagement.api.contracts import (
    IncidentView,
    NotificationView,
    OverrideRequest,
    TraceView,
)


class EngagementFacade(Protocol):
    def notifications(self, member_ref: str, limit: int) -> list[NotificationView]: ...

    def override(self, content_id: str, request: OverrideRequest, actor_ref: str) -> str: ...

    def trace(self, trace_id: str) -> TraceView | None: ...

    def incidents(self, limit: int) -> list[IncidentView]: ...


class UnavailableEngagementFacade:
    def notifications(self, member_ref: str, limit: int) -> list[NotificationView]:
        del member_ref, limit
        return []

    def override(self, content_id: str, request: OverrideRequest, actor_ref: str) -> str:
        del content_id, request, actor_ref
        raise HTTPException(status_code=503, detail="engagement persistence unavailable")

    def trace(self, trace_id: str) -> TraceView | None:
        del trace_id
        return None

    def incidents(self, limit: int) -> list[IncidentView]:
        del limit
        return []


def require_admin(x_operator_role: str | None = Header(default=None)) -> str:
    if x_operator_role != "administrator":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resource unavailable")
    return "operator-digest"


def create_engagement_router(facade: EngagementFacade) -> APIRouter:
    router = APIRouter(prefix="/api/v1/engagement", tags=["engagement"])

    @router.get("/notifications", response_model=list[NotificationView])
    def notifications(
        x_member_ref: str = Header(min_length=1), limit: int = 20
    ) -> list[NotificationView]:
        return facade.notifications(x_member_ref, min(max(limit, 1), 100))

    @router.post("/admin/content/{content_id}/override", status_code=202)
    def override(
        content_id: str,
        request: OverrideRequest,
        actor_ref: str = Depends(require_admin),
    ) -> dict[str, str]:
        return {"operationId": facade.override(content_id, request, actor_ref)}

    @router.get("/admin/traces/{trace_id}", response_model=TraceView)
    def trace(trace_id: str, actor_ref: str = Depends(require_admin)) -> TraceView:
        del actor_ref
        result = facade.trace(trace_id)
        if result is None:
            raise HTTPException(status_code=404, detail="resource unavailable")
        return result

    @router.get("/admin/incidents", response_model=list[IncidentView])
    def incidents(actor_ref: str = Depends(require_admin), limit: int = 20) -> list[IncidentView]:
        del actor_ref
        return facade.incidents(min(max(limit, 1), 100))

    return router
