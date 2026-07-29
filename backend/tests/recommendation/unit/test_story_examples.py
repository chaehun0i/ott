import pytest

from ott_feed.recommendation.application.orchestrator import RecommendationOrchestrator
from ott_feed.recommendation.domain.models import FeatureContext, Locale, ValidationState
from tests.recommendation.unit.test_ranking_validation import candidate


@pytest.mark.parametrize(
    ("story", "text", "locale"),
    [
        ("US-008", "60분 코미디", Locale.KO),
        ("US-009", "60 minutes comedy", Locale.EN),
        ("US-010", "코미디", Locale.KO),
        ("US-011", "comedy", Locale.EN),
        ("US-012", "코미디", Locale.KO),
        ("US-013", "comedy", Locale.EN),
        ("US-022", "코미디", Locale.KO),
        ("US-024", "comedy", Locale.EN),
    ],
)
def test_primary_story_has_safe_recommendation_example(
    story: str, text: str, locale: Locale
) -> None:
    del story
    states = {
        "a": {
            name: ValidationState.PASSED
            for name in ("approved", "available", "hard_conditions", "evidence")
        }
    }
    response = RecommendationOrchestrator().recommend(
        "r", text, locale, (candidate("a"),), FeatureContext(), states
    )
    assert response.items[0].content_id == "a"
