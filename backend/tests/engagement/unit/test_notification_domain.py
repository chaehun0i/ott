from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.engagement.domain.errors import InvalidTransition, StaleFencingToken
from ott_feed.engagement.domain.models import (
    Channel,
    DeliveryJob,
    JobStatus,
    NotificationEvent,
)

NOW = datetime(2026, 7, 31, tzinfo=UTC)


def make_job() -> DeliveryJob:
    return DeliveryJob(
        job_id="job-1",
        deduplication_key="member:content:new:in_app",
        event_id="event-1",
        member_ref="member-digest",
        channel=Channel.IN_APP,
        available_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def test_us019_job_claim_delivery_and_replay_safety() -> None:
    claimed = make_job().claim("worker-a", NOW, NOW + timedelta(seconds=30))
    assert (claimed.status, claimed.fencing_token) == (JobStatus.CLAIMED, 1)
    delivered = claimed.complete("worker-a", 1, delivered=True)
    assert (delivered.status, delivered.attempt_count) == (JobStatus.DELIVERED, 1)
    with pytest.raises(InvalidTransition):
        delivered.claim("worker-b", NOW, NOW + timedelta(seconds=30))


def test_expired_lease_reclaim_fences_stale_worker() -> None:
    first = make_job().claim("worker-a", NOW, NOW + timedelta(seconds=5))
    reclaimed = first.claim(
        "worker-b", NOW + timedelta(seconds=6), NOW + timedelta(seconds=36)
    )
    assert reclaimed.fencing_token == 2
    with pytest.raises(StaleFencingToken):
        reclaimed.complete("worker-a", 1, delivered=True)


def test_cancellation_is_idempotent_and_blocks_completion() -> None:
    cancelled = make_job().cancel()
    assert cancelled.cancel() == cancelled
    with pytest.raises(StaleFencingToken):
        cancelled.complete("worker-a", 1, delivered=True)


def test_notification_event_requires_ordered_lifetime() -> None:
    with pytest.raises(ValueError, match="expiry"):
        NotificationEvent("e", "c", 1, "new", NOW, NOW)
