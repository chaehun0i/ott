from __future__ import annotations

import os
import time

import pytest
from sqlalchemy import create_engine, text

from ott_feed.ingestion.application.normalization import MetadataNormalizer
from ott_feed.ingestion.application.recovery import RecoveryCoordinator, RecoverySnapshot
from ott_feed.ingestion.domain.errors import IngestionError

pytestmark = pytest.mark.integration


def _nodes(plan: dict[str, object]):
    yield str(plan["Node Type"])
    for child in plan.get("Plans", []):
        yield from _nodes(child)


def test_million_row_claim_plan_is_bounded_on_real_postgresql() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U04 capacity gate")
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TEMP TABLE u04_capacity_jobs ("
                    "job_id bigint PRIMARY KEY, provider_id integer NOT NULL, lane text NOT NULL, "
                    "status text NOT NULL, available_at timestamptz NOT NULL, "
                    "priority integer NOT NULL"
                    ") ON COMMIT DROP"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX ix_capacity_claim ON u04_capacity_jobs "
                    "(lane, status, available_at, priority, job_id)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO u04_capacity_jobs "
                    "SELECT value, value % 20, 'u04_incremental', 'scheduled', "
                    "TIMESTAMPTZ '2026-01-01 00:00:00+00' + (value % 1000) * INTERVAL '1 second', "
                    "value % 100 FROM generate_series(1, 1000000) AS value"
                )
            )
            connection.execute(text("ANALYZE u04_capacity_jobs"))
            result = connection.scalar(
                text(
                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "
                    "SELECT job_id FROM u04_capacity_jobs "
                    "WHERE lane='u04_incremental' AND status='scheduled' "
                    "AND available_at <= TIMESTAMPTZ '2026-01-01 00:20:00+00' "
                    "ORDER BY available_at, priority, job_id LIMIT 100"
                )
            )
        plan = result[0]["Plan"]
        assert any("Index" in node for node in _nodes(plan))
        assert float(plan["Actual Total Time"]) < 2_000
        assert int(plan["Actual Rows"]) == 100
    finally:
        engine.dispose()


def test_hundred_thousand_record_normalization_fits_four_hour_budget() -> None:
    normalizer = MetadataNormalizer()
    started = time.perf_counter()
    for index in range(100_000):
        normalizer.normalize(
            {
                "content_type": "movie",
                "external_ids": {"provider": str(index)},
                "titles": {"ko-KR": f"제목 {index}"},
            },
            raw_record_id=f"raw-{index}",
            normalized_id=f"normalized-{index}",
        )
    elapsed = time.perf_counter() - started
    assert elapsed < 60
    assert 100_000 / elapsed > 100_000 / (4 * 60 * 60)


def test_restore_reentry_blocks_each_invariant_family() -> None:
    coordinator = RecoveryCoordinator()
    fields = (
        "missing_policy_references",
        "missing_rule_references",
        "cursor_regressions",
        "duplicate_publication_receipts",
        "quarantine_leaks",
        "expired_raw_bodies",
    )
    for field in fields:
        with pytest.raises(IngestionError, match=field):
            coordinator.verify(RecoverySnapshot(**{field: 1}))
    pending = coordinator.verify(RecoverySnapshot())
    assert pending.publication_enabled and not pending.provider_claims_enabled
    ready = coordinator.verify(RecoverySnapshot(pending_publications_reconciled=True))
    assert ready.provider_claims_enabled
