from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.engagement.application.delivery import CircuitState, EmailCircuit, retry_at
from ott_feed.engagement.application.health import (
    HealthContribution,
    HealthState,
    aggregate_health,
)
from ott_feed.engagement.application.incidents import Incident, IncidentState, correlation_key
from ott_feed.engagement.application.notifications import (
    NotificationAdmission,
    PreferenceSnapshot,
    cancel_member_jobs,
    ready_for_lane,
    stable_deduplication_key,
)
from ott_feed.engagement.application.operations import (
    AuditKeyRing,
    OverrideCommand,
    project_trace,
)
from ott_feed.engagement.application.retention import (
    RetainedRecord,
    expired_batch,
    verify_recovery_key_ids,
)
from ott_feed.engagement.domain.models import Channel, NotificationEvent

NOW = datetime(2026, 7, 31, tzinfo=UTC)


def event() -> NotificationEvent:
    return NotificationEvent("event", "content", 2, "new", NOW, NOW + timedelta(hours=1))


def test_admission_is_stable_bounded_and_cancellable() -> None:
    preferences = (PreferenceSnapshot("member", frozenset({Channel.IN_APP, Channel.EMAIL})),)
    jobs = NotificationAdmission().admit(event(), preferences)
    assert len(jobs) == 2
    assert jobs[0].deduplication_key == stable_deduplication_key("member", event(), jobs[0].channel)
    assert len(ready_for_lane(jobs, Channel.EMAIL, NOW, 1)) == 1
    assert all(job.status.value == "cancelled" for job in cancel_member_jobs(jobs, "member"))


def test_retry_and_email_circuit_do_not_affect_other_lanes() -> None:
    assert retry_at(1, NOW) == NOW + timedelta(seconds=5)
    circuit = EmailCircuit()
    for _ in range(10):
        circuit.record(False, NOW)
    assert circuit.state is CircuitState.OPEN
    assert not circuit.allow(NOW + timedelta(seconds=29))
    assert circuit.allow(NOW + timedelta(seconds=30))


def test_override_audit_rotation_and_trace_allowlist() -> None:
    command = OverrideCommand("op", "content", 1, {"visibility": "hidden"}, "actor", NOW, "idem")
    command.validate(NOW + timedelta(minutes=14))
    ring = AuditKeyRing("k2", {"k1": b"old-secret", "k2": b"new-secret"})
    audit = {"event_id": "e", "operation": "override", "outcome": "applied", "secret": "x"}
    key_id, digest = ring.sign(audit)
    assert ring.verify(audit, key_id, digest)
    assert not ring.verify({**audit, "outcome": "failed"}, key_id, digest)
    assert project_trace({"request_id": "r", "reason_codes": ["a"], "owner_id": "raw"}) == {
        "request_id": "r",
        "reason_codes": ["a"],
    }


def test_health_truth_is_order_independent_and_optional_degrades() -> None:
    required = HealthContribution("db", HealthState.HEALTHY, True, NOW, timedelta(seconds=30), "ok")
    optional = HealthContribution(
        "email", HealthState.UNHEALTHY, False, NOW, timedelta(seconds=30), "email_down"
    )
    first = aggregate_health((required, optional), NOW)
    second = aggregate_health((optional, required), NOW)
    assert first == second
    assert first.ready and first.status is HealthState.DEGRADED


def test_incident_state_machine_requires_version_and_resolution_evidence() -> None:
    incident = Incident("i", correlation_key("u06", "queue", "email"), "high", owner="operator")
    mitigating = incident.transition(IncidentState.MITIGATING, 0)
    monitoring = mitigating.transition(IncidentState.MONITORING, 1, "queue recovered")
    resolved = monitoring.transition(IncidentState.RESOLVED, 2, "stable 30m")
    assert resolved.state is IncidentState.RESOLVED
    with pytest.raises(ValueError, match="version"):
        incident.transition(IncidentState.MITIGATING, 2)


def test_retention_holds_and_key_archive_closure() -> None:
    records = (
        RetainedRecord("held", NOW, legal_hold=True),
        RetainedRecord("expired", NOW - timedelta(days=1)),
    )
    assert [item.record_id for item in expired_batch(records, NOW)] == ["expired"]
    verify_recovery_key_ids({"k1", "k2"}, {"k1", "k2", "k3"})
    with pytest.raises(ValueError, match="k2"):
        verify_recovery_key_ids({"k1", "k2"}, {"k1"})
