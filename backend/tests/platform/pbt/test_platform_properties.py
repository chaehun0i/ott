from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ott_feed.api.contracts import ApiError
from ott_feed.platform.application.delivery import CompatibilityEvidence
from ott_feed.platform.application.idempotency import (
    IdempotencyService,
    MemoryIdempotencyRepository,
)
from ott_feed.platform.application.pagination import CursorCodec
from ott_feed.platform.domain.models import CursorPage, CursorToken, OutboxJob, RestoreAttempt
from tests.strategies.platform import fingerprints, payloads, safe_text


@given(code=safe_text, message=safe_text, correlation=safe_text)
def test_dto_json_round_trip(code: str, message: str, correlation: str) -> None:
    dto = ApiError(code=code, message=message, correlationId=correlation)
    assert ApiError.model_validate_json(dto.model_dump_json(by_alias=True)) == dto


@given(position=safe_text, tie=safe_text, fingerprint=fingerprints)
def test_cursor_round_trip(position: str, tie: str, fingerprint: str) -> None:
    codec = CursorCodec(b"0123456789abcdef")
    original = CursorToken(position, tie, fingerprint)
    assert codec.decode(codec.encode(original), fingerprint) == original


@given(items=st.lists(st.integers(), max_size=50), size=st.integers(min_value=1, max_value=50))
def test_cursor_page_bound(items: list[int], size: int) -> None:
    if len(items) <= size:
        assert len(CursorPage(tuple(items), size).items) <= size
    else:
        with pytest.raises(ValueError):
            CursorPage(tuple(items), size)


@given(payload=payloads)
def test_completed_idempotency_is_observationally_stable(payload: dict[str, object]) -> None:
    service = IdempotencyService(MemoryIdempotencyRepository())
    record = service.reserve("scope", "key", payload)
    service.complete(record, 200, {"ok": True})
    for _ in range(3):
        replay = service.reserve("scope", "key", payload)
        assert replay.response_body == {"ok": True}


@given(integrity=st.booleans(), smoke=st.booleans())
def test_restore_never_verifies_without_both_guards(integrity: bool, smoke: bool) -> None:
    attempt = RestoreAttempt(backup_id=__import__("uuid").uuid4())
    attempt.mark_loaded()
    attempt.verify_integrity(integrity)
    if integrity:
        attempt.verify_smoke(smoke)
    assert attempt.verified is (integrity and smoke)


@given(openapi=st.booleans(), migration=st.booleans(), tests=st.booleans(), scans=st.booleans())
def test_release_compatibility_matches_reference_oracle(
    openapi: bool, migration: bool, tests: bool, scans: bool
) -> None:
    evidence = CompatibilityEvidence(openapi, migration, tests, scans)
    assert evidence.accepted is (openapi and migration and tests and scans)


@given(failures=st.lists(st.booleans(), min_size=1, max_size=8))
def test_outbox_generated_commands_only_reach_valid_states(failures: list[bool]) -> None:
    job = OutboxJob("test", {}, max_attempts=len(failures))
    for should_fail in failures:
        if job.status.value in {"succeeded", "dead_letter", "cancelled"}:
            break
        job.claim("worker", timedelta(seconds=1))
        if should_fail:
            job.fail(
                "worker",
                "failure",
                None if job.attempt_count == job.max_attempts else job.available_at,
            )
        else:
            job.complete("worker")
    assert job.status.value in {"retry_wait", "succeeded", "dead_letter"}
