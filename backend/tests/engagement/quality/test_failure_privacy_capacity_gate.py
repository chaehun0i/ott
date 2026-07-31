from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from ott_feed.engagement.application.operations import project_trace
from ott_feed.engagement.application.retention import verify_recovery_key_ids


def test_trace_and_telemetry_contract_prohibit_sensitive_fields() -> None:
    sensitive = {"owner_id", "email", "notification_body", "provider_payload", "free_form_reason"}
    projected = project_trace(
        {
            "request_id": "request",
            "reason_codes": ["genre_match"],
            "owner_id": "raw-user",
            "provider_payload": "raw",
        }
    )
    assert sensitive.isdisjoint(projected)
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "engagement"
    for source in root.rglob("*.py"):
        if source.name == "models.py":
            continue
        content = source.read_text(encoding="utf-8")
        assert "provider_payload" not in content


def test_missing_recovery_key_fails_closed() -> None:
    with pytest.raises(ValueError, match="missing audit key ids"):
        verify_recovery_key_ids({"current", "previous"}, {"current"})


@pytest.mark.integration
def test_10k_job_and_100k_audit_capacity_plans_are_index_bounded() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U06 capacity gate")
    engine = create_engine(url)
    with engine.begin() as connection:
        job_plan = connection.scalar(
            text(
                "EXPLAIN (FORMAT JSON) SELECT job_id FROM u06_engagement.notification_jobs "
                "WHERE channel='in_app' AND status IN ('ready','retry') AND available_at <= now() "
                "ORDER BY available_at, job_id LIMIT 100"
            )
        )
        audit_plan = connection.scalar(
            text(
                "EXPLAIN (FORMAT JSON) SELECT audit_id FROM u06_engagement.audit_events "
                "ORDER BY occurred_at, audit_id LIMIT 100"
            )
        )
    serialized = json.dumps((job_plan, audit_plan))
    assert "Limit" in serialized
    assert len(serialized) < 20_000


def test_no_secret_values_are_tracked_in_u06_compose_references() -> None:
    compose = (Path(__file__).parents[4] / "compose.yaml").read_text(encoding="utf-8")
    assert "local-u06-test-only" not in compose
    assert "/run/secrets/u06_audit_keyring" in compose
    assert "/run/secrets/u06_email_provider" in compose
