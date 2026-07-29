from dataclasses import FrozenInstanceError

import pytest

from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import (
    Condition,
    ConditionKind,
    FeatureContext,
    Locale,
    RecommendationIntent,
)
from ott_feed.recommendation.domain.policies import DiversityPolicy, ScorePolicy


def test_condition_is_canonical_and_immutable() -> None:
    condition = Condition(ConditionKind.GENRE, " Comedy ")
    assert condition.value == "comedy"
    with pytest.raises(FrozenInstanceError):
        condition.value = "drama"  # type: ignore[misc]


def test_intent_rejects_duplicate_kind() -> None:
    with pytest.raises(RecommendationError, match="unique"):
        RecommendationIntent(
            Locale.EN,
            (
                Condition(ConditionKind.GENRE, "comedy"),
                Condition(ConditionKind.GENRE, "drama"),
            ),
        )


def test_feature_context_copies_input() -> None:
    values = {"genre:comedy": 0.7}
    context = FeatureContext(values, True, "features-1")
    values["genre:comedy"] = 0.1
    assert context.values["genre:comedy"] == 0.7


def test_policy_bounds() -> None:
    assert ScorePolicy().request_fit == 0.45
    with pytest.raises(ValueError, match="sum to one"):
        ScorePolicy(request_fit=0.5)
    with pytest.raises(ValueError, match="positive"):
        DiversityPolicy(max_per_genre=0)
