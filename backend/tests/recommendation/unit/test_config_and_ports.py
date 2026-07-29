from dataclasses import FrozenInstanceError

import pytest

from ott_feed.recommendation.config import RecommendationSettings


def test_recommendation_settings_have_approved_bounds() -> None:
    settings = RecommendationSettings()
    assert settings.total_timeout_ms == 10_000
    assert settings.max_exposed == 20
    assert settings.max_ai_response_bytes == 256 * 1024
    with pytest.raises(FrozenInstanceError):
        settings.max_exposed = 21  # type: ignore[misc]


def test_settings_reject_invalid_candidate_order() -> None:
    with pytest.raises(ValueError, match="candidate bounds"):
        RecommendationSettings(max_reserve=10, max_exposed=20)


def test_settings_reject_ai_budget_without_reserve() -> None:
    with pytest.raises(ValueError, match="deadline capacity"):
        RecommendationSettings(intent_timeout_ms=5_000, draft_timeout_ms=5_000)


def test_settings_load_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("U05_AI_CONCURRENCY", "3")
    assert RecommendationSettings.from_environment().ai_concurrency == 3
