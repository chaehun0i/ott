from ott_feed.recommendation.adapters.catalog import detach_approved_candidate
from ott_feed.recommendation.application.diversity import diversify
from ott_feed.recommendation.application.eligibility import eligible_candidates
from ott_feed.recommendation.application.evidence import build_evidence
from ott_feed.recommendation.application.ranking import rank_candidates
from ott_feed.recommendation.application.validation import candidate_passes, claim_passes
from ott_feed.recommendation.domain.models import (
    AtomicClaim,
    Condition,
    ConditionKind,
    FeatureContext,
    Locale,
    RecommendationIntent,
    ValidationState,
)
from ott_feed.recommendation.domain.policies import DiversityPolicy, ScorePolicy


def candidate(content_id: str, genre: str = "comedy", runtime: int = 55):
    return detach_approved_candidate(
        {
            "approval_state": "approved",
            "content_id": content_id,
            "metadata_version": "m1",
            "title": content_id,
            "synopsis": "safe synopsis",
            "genres": [genre],
            "runtime_minutes": runtime,
            "region": "kr",
            "ott": ["netflix"],
            "age_rating": 12,
            "freshness": 0.8,
            "popularity": 0.6,
        }
    )


def test_approved_hard_filter_precedes_ranking() -> None:
    intent = RecommendationIntent(
        Locale.KO,
        (Condition(ConditionKind.GENRE, "comedy"), Condition(ConditionKind.MAX_RUNTIME, "60")),
    )
    eligible = eligible_candidates(
        (candidate("a"), candidate("b", "drama"), candidate("c", runtime=90)), intent
    )
    assert [item.content_id for item in eligible] == ["a"]


def test_ranking_is_stable_and_consent_is_optional() -> None:
    intent = RecommendationIntent(Locale.EN, ())
    values = (candidate("b"), candidate("a"))
    ranked = rank_candidates(values, intent, FeatureContext(), ScorePolicy())
    assert [item.candidate.content_id for item in ranked] == ["b", "a"]
    assert ranked == rank_candidates(values, intent, FeatureContext(), ScorePolicy())


def test_diversity_never_invents_candidate() -> None:
    ranked = rank_candidates(
        tuple(candidate(str(i)) for i in range(5)),
        RecommendationIntent(Locale.EN, ()),
        FeatureContext(),
        ScorePolicy(),
    )
    selected, reserve = diversify(ranked, DiversityPolicy(max_per_genre=2), 4)
    assert len(selected) == 2
    assert {item.candidate.content_id for item in selected + reserve} <= {str(i) for i in range(5)}


def test_validation_is_complete_and_claim_is_candidate_local() -> None:
    item = candidate("a")
    evidence = build_evidence(item)
    assert candidate_passes(
        {
            name: ValidationState.PASSED
            for name in ("approved", "available", "hard_conditions", "evidence")
        }
    )
    assert not candidate_passes({"approved": ValidationState.PASSED})
    assert claim_passes(AtomicClaim("a", "m1", "synopsis", "safe"), evidence)
    assert not claim_passes(AtomicClaim("b", "m1", "synopsis", "unsafe"), evidence)
