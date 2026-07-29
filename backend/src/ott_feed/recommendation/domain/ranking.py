"""Pure deterministic ranking formula."""

from ott_feed.recommendation.domain.models import (
    ApprovedCandidate,
    ConditionKind,
    FeatureContext,
    RecommendationIntent,
    ScoreProof,
)
from ott_feed.recommendation.domain.policies import ScorePolicy


def score(
    candidate: ApprovedCandidate,
    intent: RecommendationIntent,
    features: FeatureContext,
    policy: ScorePolicy,
) -> ScoreProof:
    genre = intent.condition(ConditionKind.GENRE)
    request_fit = 1.0 if genre is None or genre.value in candidate.genres else 0.0
    affinity = 0.0
    if features.consented:
        affinity = max(
            (features.values.get(f"genre:{item}", 0.0) for item in candidate.genres), default=0.0
        )
    novelty = (
        max(0.0, 1.0 - features.values.get(f"seen:{candidate.content_id}", 0.0))
        if features.consented
        else 0.5
    )
    return ScoreProof(
        request_fit * policy.request_fit,
        affinity * policy.affinity,
        min(max(candidate.freshness, 0.0), 1.0) * policy.freshness,
        min(max(candidate.popularity, 0.0), 1.0) * policy.popularity,
        novelty * policy.novelty,
    )
