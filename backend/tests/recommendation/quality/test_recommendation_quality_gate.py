import json
from pathlib import Path

from ott_feed.recommendation.application.intent import deterministic_intent
from ott_feed.recommendation.application.quality import QualityResult, activation_allowed
from ott_feed.recommendation.domain.models import ConditionKind, Locale


def test_bilingual_fixture_has_identical_hard_conditions() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "bilingual-quality.json"
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    intents = [deterministic_intent(item["text"], Locale(item["locale"])) for item in fixtures]
    assert {intent.condition(ConditionKind.GENRE).value for intent in intents} == {"comedy"}
    assert {intent.condition(ConditionKind.MAX_RUNTIME).value for intent in intents} == {"60"}


def test_activation_blocks_safety_or_relevance_regression() -> None:
    active = QualityResult(1, 1, 1, 0.96)
    assert activation_allowed(active, QualityResult(1, 1, 1, 0.97))
    assert not activation_allowed(active, QualityResult(1, 1, 0.99, 0.98))
    assert not activation_allowed(active, QualityResult(1, 1, 1, 0.95))
