"""U04 API routing with injected operator authorization."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

from fastapi import APIRouter, Depends, Header

from ott_feed.ingestion.api.contracts import (
    JobStatusResponse,
    RetryRequest,
    RetryResponse,
    RuleContractResponse,
)
from ott_feed.ingestion.domain.errors import IngestionError


class IngestionFacade(Protocol):
    def current_rule_contract(self) -> Mapping[str, object]: ...

    def job_status(self, job_id: str) -> Mapping[str, object]: ...

    def retry_quarantine(
        self, quarantine_id: str, target_rule_version: str, actor_reference: str
    ) -> str: ...


class UnavailableIngestionFacade:
    def current_rule_contract(self) -> Mapping[str, object]:
        raise IngestionError(
            "U04_UNAVAILABLE", "ingestion rule contract unavailable", retryable=True
        )

    def job_status(self, job_id: str) -> Mapping[str, object]:
        raise IngestionError(
            "U04_UNAVAILABLE", f"ingestion job unavailable: {job_id}", retryable=True
        )

    def retry_quarantine(
        self, quarantine_id: str, target_rule_version: str, actor_reference: str
    ) -> str:
        raise IngestionError(
            "U04_UNAVAILABLE", f"quarantine retry unavailable: {quarantine_id}", retryable=True
        )


def create_ingestion_router(
    facade: IngestionFacade,
    operator_guard: Callable[[], None],
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

    @router.get("/rules/current", response_model=RuleContractResponse)
    def current_rules() -> Mapping[str, object]:
        return facade.current_rule_contract()

    @router.get(
        "/jobs/{job_id}",
        response_model=JobStatusResponse,
        dependencies=[Depends(operator_guard)],
    )
    def job_status(job_id: str) -> Mapping[str, object]:
        return facade.job_status(job_id)

    @router.post(
        "/quarantine/{quarantine_id}/retry",
        response_model=RetryResponse,
        dependencies=[Depends(operator_guard)],
    )
    def retry(
        quarantine_id: str,
        body: RetryRequest,
        x_actor_reference: str = Header(min_length=1, max_length=120),
    ) -> RetryResponse:
        key = facade.retry_quarantine(quarantine_id, body.target_rule_version, x_actor_reference)
        return RetryResponse(attempt_key=key)

    return router
