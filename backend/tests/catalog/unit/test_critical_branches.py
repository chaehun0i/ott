from __future__ import annotations

from uuid import uuid4

import pytest

from ott_feed.catalog.application.closure import ApprovedClosureGuard, stable_closure_error
from ott_feed.catalog.domain.errors import (
    ApprovalClosureError,
    AvailabilityError,
    ProjectionGapError,
)
from ott_feed.catalog.domain.models import CatalogState
from ott_feed.catalog.domain.policies import FeedFilters, matches_filters
from ott_feed.catalog.worker import (
    CatalogWorkerHandlers,
    IncrementalProjectionHandler,
    ProjectionEvent,
    U03LaneBudgets,
    register_catalog_handlers,
)
from ott_feed.platform.application.outbox import HandlerRegistry
from tests.catalog.unit.test_domain_and_queries import NOW, Reader, content


def test_closure_withdrawal_license_availability_and_stable_error() -> None:
    withdrawn = content()
    withdrawn.state = CatalogState.WITHDRAWN
    with pytest.raises(ApprovalClosureError) as captured:
        ApprovedClosureGuard(Reader(withdrawn)).require(withdrawn.id, "KR", NOW)
    assert stable_closure_error(captured.value) == "CAT_APPROVAL_CLOSED"

    unlicensed = content()
    object.__setattr__(unlicensed.source, "license_reference", "")
    with pytest.raises(ApprovalClosureError, match="approved"):
        ApprovedClosureGuard(Reader(unlicensed)).require(unlicensed.id, "KR", NOW)

    with pytest.raises(AvailabilityError):
        ApprovedClosureGuard(Reader(content())).require("c1", "US", NOW)


def test_all_filter_rejection_branches() -> None:
    item = content()
    item.state = CatalogState.WITHDRAWN
    assert not matches_filters(item, FeedFilters(), "KR", NOW)
    item.state = CatalogState.APPROVED
    assert not matches_filters(item, FeedFilters(), "US", NOW)
    assert not matches_filters(item, FeedFilters(content_types=frozenset({"series"})), "KR", NOW)
    assert not matches_filters(item, FeedFilters(genres=frozenset({"drama"})), "KR", NOW)
    assert not matches_filters(item, FeedFilters(providers=frozenset({"other"})), "KR", NOW)
    assert not matches_filters(item, FeedFilters(max_runtime_minutes=30), "KR", NOW)
    item.runtime_minutes = None
    assert not matches_filters(item, FeedFilters(max_runtime_minutes=30), "KR", NOW)


class ProjectionRepository:
    def __init__(self) -> None:
        self.received = False
        self.version = 0
        self.advance_result = True
        self.gaps: list[int] = []
        self.receipts: list[int] = []

    def has_receipt(self, event_id, projection: str) -> bool:
        return self.received

    def contiguous_version(self, projection: str) -> int:
        return self.version

    def record_gap(self, projection: str, missing_version: int) -> None:
        self.gaps.append(missing_version)

    def advance(self, projection: str, expected: int, version: int) -> bool:
        return self.advance_result

    def receipt(self, event_id, projection: str, content_id: str, version: int) -> None:
        self.receipts.append(version)


def test_projection_receipt_old_gap_cas_and_success_paths() -> None:
    repository = ProjectionRepository()
    applied: list[int] = []
    replayed: list[int] = []
    handler = IncrementalProjectionHandler(
        repository, "feed", lambda event: applied.append(event.catalog_version), replayed.append
    )
    event = ProjectionEvent(uuid4(), "c1", 1)
    repository.received = True
    handler(event)
    assert not applied
    repository.received = False
    handler(ProjectionEvent(uuid4(), "c1", 0))
    assert not applied
    with pytest.raises(ProjectionGapError):
        handler(ProjectionEvent(uuid4(), "c1", 2))
    assert repository.gaps == [1] and replayed == [1]
    repository.advance_result = False
    with pytest.raises(ProjectionGapError):
        handler(event)
    repository.advance_result = True
    handler(event)
    assert applied[-1] == 1 and repository.receipts == [1]


def test_worker_budgets_and_registration_paths() -> None:
    with pytest.raises(ValueError):
        U03LaneBudgets(incremental=0)
    budgets = U03LaneBudgets(incremental=1)
    calls: list[dict[str, object]] = []
    bounded = budgets.wrap("incremental", calls.append)
    bounded({"ok": True})
    assert calls == [{"ok": True}]
    semaphore = budgets._budgets["incremental"]
    assert semaphore.acquire(blocking=False)
    try:
        with pytest.raises(RuntimeError, match="saturated"):
            bounded({})
    finally:
        semaphore.release()

    registry = HandlerRegistry()
    register_catalog_handlers(
        registry,
        CatalogWorkerHandlers(lambda payload: None, lambda payload: None),
        budgets,
    )
    assert registry.job_types == (
        "u03.projection.incremental-feed",
        "u03.projection.replay-gap",
    )
