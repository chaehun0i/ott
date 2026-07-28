import pytest

from ott_feed.ingestion.health import IngestionHealthContributor
from ott_feed.ingestion.telemetry import safe_attributes
from ott_feed.ingestion.worker import IngestionWorkerHandlers, U04LaneBudgets
from ott_feed.platform.health import HealthRegistry
from ott_feed.worker import build_worker_registry


def test_six_worker_lanes_are_registered_with_budget() -> None:
    seen: list[dict[str, object]] = []

    def handler(payload: dict[str, object]) -> None:
        seen.append(payload)

    handlers = IngestionWorkerHandlers(handler, handler, handler, handler, handler, handler)
    registry = build_worker_registry(
        ingestion_handlers=handlers, u04_budgets=U04LaneBudgets(incremental=3)
    )
    assert set(registry.job_types) == {
        "u04.withdrawal",
        "u04.publication",
        "u04.incremental",
        "u04.revalidation",
        "u04.full_sync",
        "u04.retention",
    }
    registry._handlers["u04.incremental"]({"job_id": "job"})
    assert seen == [{"job_id": "job", "_budget": 3}]


def test_lane_budgets_fail_fast() -> None:
    with pytest.raises(ValueError):
        U04LaneBudgets(publication=0)


def test_health_layers_and_telemetry_drop_sensitive_attributes() -> None:
    health = HealthRegistry()
    IngestionHealthContributor(lambda: True, lambda: True, lambda: True, lambda: True).register(
        health
    )
    assert health.readiness().status == "ready"
    assert health.deep().checks["u04_provider_degraded"] == "down"
    attributes = safe_attributes(
        {
            "provider_id": "provider",
            "outcome": "passed",
            "payload_body": "secret",
            "provider_token": "secret",
            "url_query": "secret",
        }
    )
    assert attributes == {"provider_id": "provider", "outcome": "passed"}
