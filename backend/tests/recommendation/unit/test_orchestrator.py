import pytest

from ott_feed.recommendation.application.orchestrator import RecommendationOrchestrator
from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import FeatureContext, Locale, ValidationState
from tests.recommendation.unit.test_ranking_validation import candidate


def valid(content_id: str) -> dict[str, dict[str, ValidationState]]:
    return {
        content_id: {
            name: ValidationState.PASSED
            for name in ("approved", "available", "hard_conditions", "evidence")
        }
    }


def test_pipeline_returns_only_completely_validated_candidates() -> None:
    response = RecommendationOrchestrator().recommend(
        "r1",
        "60분 코미디",
        Locale.KO,
        (candidate("a"), candidate("b", "drama")),
        FeatureContext(),
        valid("a"),
    )
    assert [item.content_id for item in response.items] == ["a"]
    assert {reason.value for reason in response.degraded_reasons} == {
        "ai_unavailable",
        "non_personalized",
    }


def test_catalog_failure_is_fail_closed() -> None:
    with pytest.raises(RecommendationError, match="catalog"):
        RecommendationOrchestrator().recommend("r", "comedy", Locale.EN, None)


def test_deadline_is_bounded() -> None:
    ticks = iter((0.0, 11.0))
    with pytest.raises(RecommendationError, match="deadline"):
        RecommendationOrchestrator(monotonic=lambda: next(ticks)).recommend(
            "r", "comedy", Locale.EN, (), FeatureContext(consented=True), {}
        )
