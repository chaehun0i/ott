from __future__ import annotations

from dataclasses import replace

import pytest

from ott_feed.identity.config import IdentitySettings
from ott_feed.identity.telemetry import IdentityTelemetry, validate_labels
from ott_feed.identity.worker import IdentityWorkerHandlers
from ott_feed.platform.config import Settings
from ott_feed.platform.domain.models import OutboxJob
from ott_feed.platform.health import HealthRegistry, IdentityHealthContributor
from ott_feed.platform.telemetry import Metrics, NonBlockingTelemetryBuffer
from ott_feed.worker import build_worker_registry


def test_identity_workers_register_all_bounded_lanes() -> None:
    handled: list[str] = []

    def handler(payload: dict[str, object]) -> None:
        handled.append(str(payload["kind"]))

    handlers = IdentityWorkerHandlers(handler, handler, handler, handler, handler, handler)
    identity_settings = replace(
        IdentitySettings.from_environment("local"),
        worker_high_limit=1,
        worker_normal_limit=1,
        worker_low_limit=1,
    )
    registry = build_worker_registry(
        Settings("local", "sqlite+pysqlite:///:memory:", "localhost", b"secret"),
        handlers,
        identity_settings,
    )

    assert set(registry.job_types) == {
        "identity.feature.explicit-refresh",
        "identity.feature.implicit-event",
        "identity.consent.withdrawal-cleanup",
        "identity.data-rights.deletion",
        "identity.data-rights.export",
        "identity.key-rotation",
    }
    registry.handle(OutboxJob("identity.data-rights.deletion", {"kind": "deletion"}))
    assert handled == ["deletion"]


@pytest.mark.parametrize(
    "labels",
    [
        {"email": "member@example.test"},
        {"userId": "user-1"},
        {"oauth_subject": "provider-subject"},
        {"session_token": "opaque"},
        {"session_id": "session-1"},
        {"payload": "raw"},
        {"object_reference": "exports/private"},
    ],
)
def test_telemetry_rejects_direct_identifier_and_secret_labels(
    labels: dict[str, str],
) -> None:
    with pytest.raises(ValueError):
        validate_labels(labels)


def test_telemetry_accepts_only_bounded_operational_dimensions() -> None:
    telemetry = IdentityTelemetry(Metrics(), NonBlockingTelemetryBuffer(2))

    telemetry.record(
        "ott_identity_job_total",
        component="deletion_worker",
        operation="delete_category",
        lane="high",
        result="completed",
    )

    assert len(telemetry.metrics.snapshot()) == 1
    assert telemetry.events.drain()[0]["component"] == "deletion_worker"


def test_identity_health_separates_readiness_from_deep_provider_detail() -> None:
    registry = HealthRegistry()
    IdentityHealthContributor(
        database=lambda: True,
        worker_backlog_ok=lambda: True,
        google_circuit_ok=lambda: False,
        argon2_capacity_ok=lambda: True,
    ).register(registry)

    assert registry.readiness().status == "ready"
    assert registry.deep().status == "degraded"
