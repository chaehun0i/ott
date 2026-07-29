import time
from pathlib import Path

from ott_feed.recommendation.adapters.persistence.models import RecommendationTraceRow
from ott_feed.recommendation.application.eligibility import eligible_candidates
from ott_feed.recommendation.application.orchestrator import RecommendationOrchestrator
from ott_feed.recommendation.domain.models import Locale, RecommendationIntent
from ott_feed.recommendation.telemetry import ALLOWED_ATTRIBUTES
from tests.recommendation.unit.test_ranking_validation import candidate


def test_hundred_thousand_candidate_filter_is_bounded() -> None:
    values = tuple(candidate(str(index)) for index in range(100_000))
    started = time.perf_counter()
    result = eligible_candidates(values, RecommendationIntent(Locale.EN, ()))
    assert len(result) == 100_000
    assert time.perf_counter() - started < 5.0


def test_burst_fifteen_deterministic_requests_is_bounded() -> None:
    started = time.perf_counter()
    for index in range(15):
        RecommendationOrchestrator().recommend(str(index), "comedy", Locale.EN, (), validation={})
    assert time.perf_counter() - started < 3.0


def test_persistence_and_telemetry_have_no_prohibited_payload_fields() -> None:
    prohibited = {"prompt", "response_body", "draft", "chain_of_thought", "email", "user_id"}
    assert prohibited.isdisjoint(
        {column.name for column in RecommendationTraceRow.__table__.columns}
    )
    assert prohibited.isdisjoint(ALLOWED_ATTRIBUTES)
    source = (
        Path(__file__).parents[3] / "src" / "ott_feed" / "recommendation" / "telemetry.py"
    ).read_text(encoding="utf-8")
    assert "request_text" not in source and "synopsis" not in source
