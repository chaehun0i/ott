"""Hard eligibility predicates always applied before ranking."""

from ott_feed.recommendation.domain.models import (
    ApprovedCandidate,
    ConditionKind,
    RecommendationIntent,
)


def is_eligible(candidate: ApprovedCandidate, intent: RecommendationIntent) -> bool:
    genre = intent.condition(ConditionKind.GENRE)
    runtime = intent.condition(ConditionKind.MAX_RUNTIME)
    region = intent.condition(ConditionKind.REGION)
    ott = intent.condition(ConditionKind.OTT)
    age = intent.condition(ConditionKind.AGE_RATING)
    return not (
        (genre and genre.value not in candidate.genres)
        or (runtime and candidate.runtime_minutes > int(runtime.value))
        or (region and region.value != candidate.region.casefold())
        or (ott and ott.value not in candidate.ott)
        or (age and candidate.age_rating > int(age.value))
    )


def eligible_candidates(
    candidates: tuple[ApprovedCandidate, ...], intent: RecommendationIntent
) -> tuple[ApprovedCandidate, ...]:
    return tuple(candidate for candidate in candidates if is_eligible(candidate, intent))
