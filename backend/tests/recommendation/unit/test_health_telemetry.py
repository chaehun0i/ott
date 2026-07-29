from ott_feed.platform.health import HealthRegistry
from ott_feed.recommendation.health import RecommendationHealthContributor
from ott_feed.recommendation.telemetry import UsageMeasurement, safe_attributes


def test_telemetry_drops_payload_and_identity_fields() -> None:
    values = safe_attributes({"outcome": "fallback", "request_text": "secret", "user_id": "direct"})
    assert values == {"outcome": "fallback"}


def test_usage_cost_has_no_prompt_content() -> None:
    usage = UsageMeasurement("model-1", 10, 5, 0.001)
    assert usage.estimated_cost == 0.015
    assert not hasattr(usage, "prompt")


def test_ai_and_features_are_degradable_health() -> None:
    registry = HealthRegistry()
    RecommendationHealthContributor(
        lambda: True, lambda: True, lambda: True, lambda: False, lambda: False
    ).register(registry)
    assert registry.readiness().status == "ready"
    assert registry.deep().checks["u05_ai"] == "down"
