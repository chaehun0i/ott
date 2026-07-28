from __future__ import annotations

import os
from time import monotonic

import pytest
from sqlalchemy import create_engine, text

from ott_feed.search.application.quality import QualityResult, ndcg_at_k, recall_at_k

pytestmark = pytest.mark.integration


def test_100k_capacity_plan_and_bilingual_quality_thresholds() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U03 PostgreSQL gate")
    engine = create_engine(url)
    started = monotonic()
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TEMP TABLE u03_capacity AS "
                "SELECT n::text AS content_id, (n % 1000)::float / 1000 AS score "
                "FROM generate_series(1, 100000) n"
            )
        )
        connection.execute(text("CREATE INDEX ON u03_capacity (score DESC, content_id)"))
        count = connection.scalar(text("SELECT count(*) FROM u03_capacity"))
        plan = "\n".join(
            connection.scalars(
                text(
                    "EXPLAIN (COSTS OFF) SELECT content_id FROM u03_capacity "
                    "ORDER BY score DESC, content_id LIMIT 20"
                )
            )
        )
    elapsed = monotonic() - started
    engine.dispose()
    assert count == 100000 and "Index" in plan
    assert elapsed < 60

    korean_actual = ["k1", "k2", "k3", "x"]
    english_actual = ["e1", "e2", "e3", "x"]
    recall = min(
        recall_at_k(korean_actual, frozenset({"k1", "k2", "k3"})),
        recall_at_k(english_actual, frozenset({"e1", "e2", "e3"})),
    )
    ndcg = min(
        ndcg_at_k(korean_actual, frozenset({"k1", "k2", "k3"})),
        ndcg_at_k(english_actual, frozenset({"e1", "e2", "e3"})),
    )
    result = QualityResult(recall, ndcg, 1.0, 0, 0, elapsed * 1000)
    assert result.passes(recall_threshold=0.85, ndcg_threshold=0.80, latency_threshold_ms=60000)
