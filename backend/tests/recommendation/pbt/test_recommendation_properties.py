import pytest
from hypothesis import given
from hypothesis import strategies as st

from ott_feed.recommendation.application.diversity import diversify
from ott_feed.recommendation.application.eligibility import eligible_candidates
from ott_feed.recommendation.application.evidence import build_evidence
from ott_feed.recommendation.application.intent import deterministic_intent
from ott_feed.recommendation.application.ranking import rank_candidates
from ott_feed.recommendation.application.resilience import AICircuit
from ott_feed.recommendation.application.validation import candidate_passes
from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import (
    FeatureContext,
    Locale,
    RecommendationIntent,
    ValidationState,
)
from ott_feed.recommendation.domain.policies import DiversityPolicy, ScorePolicy
from tests.strategies.recommendation import candidates, intents

pytestmark = pytest.mark.pbt


@given(st.sampled_from(("코미디", "comedy")))
def test_p_u05_01_canonical_genre(text: str) -> None:
    assert deterministic_intent(text, Locale.KO).conditions[0].value == "comedy"


@given(st.text(max_size=100))
def test_p_u05_02_input_is_bounded(text: str) -> None:
    assert len(deterministic_intent(text, Locale.EN).conditions) <= 32


@given(intents())
def test_p_u05_03_intent_is_replayable(intent: RecommendationIntent) -> None:
    assert intent == RecommendationIntent(intent.locale, intent.conditions)


@given(st.lists(candidates(), min_size=0, max_size=20), intents())
def test_p_u05_04_eligibility_is_subset(values, intent) -> None:
    assert set(eligible_candidates(tuple(values), intent)) <= set(values)


@given(
    st.lists(candidates(), min_size=0, max_size=20, unique_by=lambda item: item.content_id),
    intents(),
)
def test_p_u05_05_ranking_is_deterministic(values, intent) -> None:
    args = (tuple(values), intent, FeatureContext(), ScorePolicy())
    assert rank_candidates(*args) == rank_candidates(*args)


@given(candidates(), intents())
def test_p_u05_06_no_consent_removes_affinity(value, intent) -> None:
    ranked = rank_candidates(
        (value,), intent, FeatureContext({"genre:comedy": 1.0}, False), ScorePolicy()
    )
    assert ranked[0].proof.affinity == 0


@given(candidates(), intents(), st.floats(min_value=0, max_value=1))
def test_p_u05_07_popularity_score_is_monotonic(value, intent, popularity) -> None:
    low = value.__class__(
        value.content_id,
        value.metadata_version,
        value.title,
        value.synopsis,
        value.genres,
        value.runtime_minutes,
        value.region,
        value.ott,
        value.age_rating,
        value.freshness,
        0.0,
    )
    high = value.__class__(
        low.content_id,
        low.metadata_version,
        low.title,
        low.synopsis,
        low.genres,
        low.runtime_minutes,
        low.region,
        low.ott,
        low.age_rating,
        low.freshness,
        popularity,
    )
    assert (
        rank_candidates((high,), intent, FeatureContext(), ScorePolicy())[0].proof.total
        >= rank_candidates((low,), intent, FeatureContext(), ScorePolicy())[0].proof.total
    )


@given(st.lists(candidates(), min_size=0, max_size=20, unique_by=lambda item: item.content_id))
def test_p_u05_08_diversity_never_invents(values) -> None:
    ranked = rank_candidates(
        tuple(values), RecommendationIntent(Locale.EN, ()), FeatureContext(), ScorePolicy()
    )
    selected, reserve = diversify(ranked, DiversityPolicy(), 10)
    assert {item.candidate for item in selected + reserve} <= set(values)


@given(candidates())
def test_p_u05_09_evidence_is_candidate_local(value) -> None:
    evidence = build_evidence(value)
    assert (
        evidence.content_id == value.content_id
        and evidence.metadata_version == value.metadata_version
    )


@given(
    st.dictionaries(
        st.sampled_from(("approved", "available", "hard_conditions", "evidence")),
        st.sampled_from(tuple(ValidationState)),
        max_size=4,
    )
)
def test_p_u05_10_incomplete_validation_fails_closed(results) -> None:
    if set(results) != {"approved", "available", "hard_conditions", "evidence"} or set(
        results.values()
    ) != {ValidationState.PASSED}:
        assert not candidate_passes(results)


def test_p_u05_12_circuit_fails_fast() -> None:
    circuit = AICircuit(window=2)
    circuit.record(False)
    circuit.record(False)
    with pytest.raises(RecommendationError):
        circuit.allow()
