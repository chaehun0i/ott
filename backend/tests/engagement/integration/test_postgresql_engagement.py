from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ott_feed.engagement.adapters.persistence.models import NotificationJobRow
from ott_feed.engagement.adapters.persistence.repositories import NotificationJobRepository

pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U06 PostgreSQL gate")
    return value


def test_u06_schema_head_constraints_and_append_only_audit() -> None:
    engine = create_engine(database_url())
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0006_u06_engagement_expand"
        )
        connection.execute(
            text(
                "INSERT INTO u06_engagement.audit_events "
                "(event_id, occurred_at, actor_ref, operation, outcome, canonical_event, "
                "schema_version, key_id, digest) VALUES "
                "('u06-audit-integration', now(), 'actor', 'verify', 'ok', '{}', 1, 'k1', "
                "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa') "
                "ON CONFLICT (event_id) DO NOTHING"
            )
        )
    with engine.begin() as connection, pytest.raises(Exception, match="append-only"):
        connection.execute(
            text(
                "UPDATE u06_engagement.audit_events SET outcome='changed' "
                "WHERE event_id='u06-audit-integration'"
            )
        )


def test_claim_and_fencing_completion_on_real_postgresql() -> None:
    engine = create_engine(database_url())
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.execute(
            text("DELETE FROM u06_engagement.notification_jobs WHERE job_id='u06-job-integration'")
        )
        session.add(
            NotificationJobRow(
                job_id="u06-job-integration",
                deduplication_key="b" * 64,
                event_id="event",
                member_ref="member",
                channel="in_app",
                status="ready",
                available_at=now,
                expires_at=now + timedelta(hours=1),
                attempt_count=0,
                fencing_token=0,
            )
        )
        session.commit()
        repository = NotificationJobRepository(session)
        claimed = repository.claim("in_app", "worker-a", now, now + timedelta(seconds=30), 100)
        assert len(claimed) == 1 and claimed[0].fencing_token == 1
        session.commit()
        assert not repository.complete("u06-job-integration", "stale", 0, "delivered")
        assert repository.complete("u06-job-integration", "worker-a", 1, "delivered")
        session.commit()
