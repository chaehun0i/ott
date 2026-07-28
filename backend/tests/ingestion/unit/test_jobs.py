from datetime import UTC, datetime

import pytest

from ott_feed.ingestion.application.cursors import CursorCheckpoint, replay_start
from ott_feed.ingestion.application.jobs import JobLifecycle, PageOutcome
from ott_feed.ingestion.domain.errors import IngestionError
from ott_feed.ingestion.domain.models import IngestionJob, JobStatus

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def running_job() -> tuple[IngestionJob, JobLifecycle]:
    job = IngestionJob("job-1", "provider-1", "policy-1", "start")
    job.claim("worker-1", NOW)
    return job, JobLifecycle()


def test_page_advances_only_after_counts_reconcile() -> None:
    job, lifecycle = running_job()
    token = lifecycle.token(job)
    outcome = PageOutcome("next", frozenset({"a"}), frozenset({"b"}), frozenset())
    assert lifecycle.apply_page(job, token, "page-1", frozenset({"a", "b"}), outcome)
    assert job.durable_cursor == "next"
    assert (job.succeeded_count, job.quarantined_count) == (1, 1)


def test_duplicate_page_is_idempotent() -> None:
    job, lifecycle = running_job()
    token = lifecycle.token(job)
    outcome = PageOutcome("next", frozenset({"a"}), frozenset(), frozenset())
    assert lifecycle.apply_page(job, token, "page-1", frozenset({"a"}), outcome)
    assert not lifecycle.apply_page(job, token, "page-1", frozenset({"a"}), outcome)
    assert job.succeeded_count == 1


def test_count_mismatch_and_stale_claim_fail_closed() -> None:
    job, lifecycle = running_job()
    token = lifecycle.token(job)
    with pytest.raises(IngestionError, match="reconcile"):
        lifecycle.apply_page(
            job,
            token,
            "page-1",
            frozenset({"a", "b"}),
            PageOutcome("next", frozenset({"a"}), frozenset(), frozenset()),
        )
    lifecycle.crash(job, token)
    job.claim("worker-2", NOW)
    with pytest.raises(IngestionError, match="stale"):
        lifecycle.finish(job, token, NOW)


def test_finish_classifies_complete_job_and_clears_worker() -> None:
    job, lifecycle = running_job()
    token = lifecycle.token(job)
    lifecycle.apply_page(
        job,
        token,
        "page-1",
        frozenset({"a"}),
        PageOutcome(None, frozenset({"a"}), frozenset(), frozenset()),
    )
    lifecycle.finish(job, token, NOW)
    assert job.status is JobStatus.SUCCEEDED
    assert job.worker_id is None


def test_cursor_checkpoint_is_order_independent_and_replay_prefers_durable() -> None:
    left = CursorCheckpoint("provider", "start", "next", ("b", "a"))
    right = CursorCheckpoint("provider", "start", "next", ("a", "b"))
    assert left.page_digest == right.page_digest
    assert replay_start("durable", "configured") == "durable"
    assert replay_start(None, "configured") == "configured"
