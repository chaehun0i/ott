from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ott_feed.engagement.application.delivery import EmailCircuit, retry_at
from ott_feed.engagement.application.health import aggregate_health
from ott_feed.engagement.application.incidents import Incident, IncidentState, correlation_key
from ott_feed.engagement.application.notifications import stable_deduplication_key
from ott_feed.engagement.application.operations import (
    AuditKeyRing,
    canonical_audit_bytes,
    project_trace,
)
from ott_feed.engagement.application.retention import RetainedRecord, expired_batch
from ott_feed.engagement.domain.errors import StaleFencingToken
from ott_feed.engagement.domain.models import Channel
from tests.engagement.pbt.strategies import base_times, events, health_contributions, jobs, safe_ids

pytestmark = pytest.mark.pbt


@given(safe_ids, events(), st.sampled_from(list(Channel)))
def test_p_u06_01_dedup_is_deterministic(member: str, event, channel: Channel) -> None:
    assert stable_deduplication_key(member, event, channel) == stable_deduplication_key(
        member, event, channel
    )


@given(jobs(), safe_ids, base_times)
def test_p_u06_02_claim_increases_fence(job, owner: str, now) -> None:
    if now < job.available_at or now >= job.expires_at:
        now = job.available_at
    claimed = job.claim(owner, now, now + timedelta(seconds=30))
    assert claimed.fencing_token == job.fencing_token + 1


@given(jobs(), safe_ids, safe_ids)
def test_p_u06_03_stale_owner_never_completes(job, owner: str, stale: str) -> None:
    claimed = job.claim(owner, job.available_at, job.available_at + timedelta(seconds=30))
    if stale == owner:
        stale += "x"
    with pytest.raises(StaleFencingToken):
        claimed.complete(stale, claimed.fencing_token, True)


@given(jobs())
def test_p_u06_04_cancel_is_idempotent(job) -> None:
    assert job.cancel().cancel() == job.cancel()


@given(st.integers(min_value=1, max_value=3), base_times, st.floats(min_value=0, max_value=1))
def test_p_u06_05_retry_is_future_and_bounded(attempt: int, now, jitter: float) -> None:
    scheduled = retry_at(attempt, now, jitter)
    assert now < scheduled <= now + timedelta(minutes=6)


@given(st.lists(st.booleans(), min_size=10, max_size=20), base_times)
def test_p_u06_06_email_circuit_threshold(results: list[bool], now) -> None:
    circuit = EmailCircuit()
    for result in results:
        circuit.record(result, now)
    should_open = any(
        sum(not result for result in results[:size]) / size >= 0.5
        for size in range(10, len(results) + 1)
    )
    assert (circuit.state.value == "open") == should_open


@given(st.dictionaries(safe_ids, safe_ids, max_size=10))
def test_p_u06_07_canonical_audit_is_order_independent(values: dict[str, str]) -> None:
    event = {**values, "event_id": "e", "operation": "op", "outcome": "ok"}
    assert canonical_audit_bytes(event) == canonical_audit_bytes(
        dict(reversed(tuple(event.items())))
    )


@given(st.dictionaries(safe_ids, safe_ids, max_size=10))
def test_p_u06_08_hmac_detects_allowlisted_change(extra: dict[str, str]) -> None:
    ring = AuditKeyRing("k", {"k": b"property-secret"})
    event = {**extra, "event_id": "e", "operation": "op", "outcome": "ok"}
    key, digest = ring.sign(event)
    assert ring.verify(event, key, digest)
    assert not ring.verify({**event, "outcome": "failed"}, key, digest)


@given(st.dictionaries(safe_ids, st.one_of(safe_ids, st.lists(safe_ids)), max_size=20))
def test_p_u06_09_trace_never_exposes_unknown_fields(trace: dict[str, object]) -> None:
    assert set(project_trace(trace)).issubset(
        {"request_id", "policy_versions", "reason_codes", "outcome"}
    )


@given(st.lists(health_contributions(), max_size=12), base_times)
def test_p_u06_10_health_is_permutation_invariant(items, now) -> None:
    assert aggregate_health(tuple(items), now) == aggregate_health(tuple(reversed(items)), now)


@given(safe_ids, safe_ids, safe_ids)
def test_p_u06_11_incident_correlation_is_stable(service: str, symptom: str, scope: str) -> None:
    assert correlation_key(service, symptom, scope) == correlation_key(service, symptom, scope)
    incident = Incident("i", correlation_key(service, symptom, scope), "high", owner="owner")
    with pytest.raises(ValueError, match="invalid"):
        incident.transition(IncidentState.RESOLVED, 0, "evidence")


@given(
    st.lists(safe_ids, unique=True, max_size=30), base_times, st.integers(min_value=1, max_value=30)
)
def test_p_u06_12_retention_is_bounded_ordered_and_hold_safe(ids, now, limit: int) -> None:
    records = tuple(
        RetainedRecord(item, now - timedelta(seconds=index + 1), legal_hold=index % 3 == 0)
        for index, item in enumerate(ids)
    )
    result = expired_batch(records, now, limit)
    assert len(result) <= limit
    assert not any(item.legal_hold for item in result)
    assert list(result) == sorted(result, key=lambda item: (item.expires_at, item.record_id))
