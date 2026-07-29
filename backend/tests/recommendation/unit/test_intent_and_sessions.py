import pytest

from ott_feed.recommendation.application.intent import deterministic_intent
from ott_feed.recommendation.application.sessions import RecommendationSession
from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import ConditionKind, Locale, RecommendationIntent


def test_korean_and_english_intents_share_canonical_values() -> None:
    korean = deterministic_intent("1시간 코미디", Locale.KO)
    english = deterministic_intent("60 minutes comedy", Locale.EN)
    assert [(item.kind, item.value) for item in korean.conditions] == [
        (item.kind, item.value) for item in english.conditions
    ]


def test_session_patch_conflict_idempotency_and_reset() -> None:
    session = RecommendationSession("s1", "owner", 0, 0, RecommendationIntent(Locale.KO, ()))
    patched = session.patch({ConditionKind.GENRE: "Comedy"}, 0, "key-1")
    assert patched.version == 1
    assert patched.patch({ConditionKind.GENRE: "drama"}, 0, "key-1") == patched
    with pytest.raises(RecommendationError, match="version conflict"):
        patched.patch({ConditionKind.GENRE: "drama"}, 0, "key-2")
    reset = patched.reset(1, "key-3")
    assert reset.epoch == 1 and not reset.intent.conditions


def test_patch_reports_explicit_conflict() -> None:
    session = RecommendationSession("s1", "owner", 0, 0, deterministic_intent("코미디", Locale.KO))
    patched = session.patch({ConditionKind.GENRE: "drama"}, 0, "key")
    assert patched.intent.conflicts[0].previous == "comedy"
