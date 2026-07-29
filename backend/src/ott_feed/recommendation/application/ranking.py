"""Stable ranking application service."""

from ott_feed.recommendation.domain.models import (
    ApprovedCandidate,
    FeatureContext,
    RankedCandidate,
    RecommendationIntent,
)
from ott_feed.recommendation.domain.policies import ScorePolicy
from ott_feed.recommendation.domain.ranking import score


def rank_candidates(
    candidates: tuple[ApprovedCandidate, ...],
    intent: RecommendationIntent,
    features: FeatureContext,
    policy: ScorePolicy,
    limit: int = 500,
) -> tuple[RankedCandidate, ...]:
    ranked = tuple(
        RankedCandidate(candidate, score(candidate, intent, features, policy), position)
        for position, candidate in enumerate(candidates[:limit])
    )
    return tuple(
        sorted(
            ranked,
            key=lambda item: (-item.proof.total, item.original_position, item.candidate.content_id),
        )
    )
