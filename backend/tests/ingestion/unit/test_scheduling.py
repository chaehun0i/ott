from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.ingestion.application.scheduling import ProviderFairScheduler, ScheduledWork
from ott_feed.ingestion.domain.errors import PolicyViolation
from ott_feed.ingestion.domain.models import ProviderPolicy, ProviderPolicyStatus
from ott_feed.ingestion.domain.policies import BackpressureState, require_collection

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def policy(**changes: object) -> ProviderPolicy:
    values: dict[str, object] = {
        "policy_id": "policy-1",
        "provider_id": "provider-1",
        "version": 1,
        "status": ProviderPolicyStatus.ACTIVE,
        "allowed_uses": frozenset({"collect", "display"}),
        "regions": frozenset({"KR"}),
        "retention_seconds": 86_400,
        "refresh_seconds": 3_600,
        "effective_from": NOW,
    }
    values.update(changes)
    return ProviderPolicy(**values)  # type: ignore[arg-type]


def test_collection_requires_active_use_and_region() -> None:
    require_collection(policy(), "KR", NOW)
    with pytest.raises(PolicyViolation, match="region"):
        require_collection(policy(), "US", NOW)
    with pytest.raises(PolicyViolation, match="not active"):
        require_collection(policy(status=ProviderPolicyStatus.SUSPENDED), "KR", NOW)


def test_scheduler_reserves_publication_during_backpressure() -> None:
    candidates = (
        ScheduledWork("incremental-a", "a", "u04_incremental", NOW),
        ScheduledWork("publication-b", "b", "u04_publication", NOW),
        ScheduledWork("withdrawal-c", "c", "u04_withdrawal", NOW),
    )
    selected = ProviderFairScheduler().select(
        candidates, NOW, 10, BackpressureState(memory_ratio=0.8)
    )
    assert [item.work_id for item in selected] == ["withdrawal-c", "publication-b"]


def test_scheduler_round_robins_providers_within_lane() -> None:
    candidates = (
        ScheduledWork("a-1", "a", "u04_incremental", NOW),
        ScheduledWork("a-2", "a", "u04_incremental", NOW),
        ScheduledWork("b-1", "b", "u04_incremental", NOW),
        ScheduledWork("future", "c", "u04_incremental", NOW + timedelta(seconds=1)),
    )
    selected = ProviderFairScheduler().select(
        candidates, NOW, 3, BackpressureState(), provider_offset=1
    )
    assert [item.work_id for item in selected] == ["b-1", "a-1", "a-2"]


def test_unknown_lane_and_invalid_pressure_fail_fast() -> None:
    with pytest.raises(ValueError, match="unknown"):
        ScheduledWork("work", "provider", "unknown", NOW)
    with pytest.raises(ValueError, match="ratios"):
        BackpressureState(memory_ratio=1.1)
