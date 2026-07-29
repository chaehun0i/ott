"""Deterministic diversity reranking without candidate invention."""

from collections import Counter

from ott_feed.recommendation.domain.models import RankedCandidate
from ott_feed.recommendation.domain.policies import DiversityPolicy


def diversify(
    ranked: tuple[RankedCandidate, ...], policy: DiversityPolicy, limit: int
) -> tuple[tuple[RankedCandidate, ...], tuple[RankedCandidate, ...]]:
    selected: list[RankedCandidate] = []
    reserve: list[RankedCandidate] = []
    genres: Counter[str] = Counter()
    providers: Counter[str] = Counter()
    franchises: Counter[str] = Counter()
    for item in ranked:
        candidate = item.candidate
        genre = candidate.genres[0] if candidate.genres else "unknown"
        provider = candidate.ott[0] if candidate.ott else "unknown"
        franchise = candidate.franchise or candidate.content_id
        allowed = (
            genres[genre] < policy.max_per_genre
            and providers[provider] < policy.max_per_ott
            and franchises[franchise] < policy.max_per_franchise
        )
        if allowed and len(selected) < limit:
            selected.append(item)
            genres[genre] += 1
            providers[provider] += 1
            franchises[franchise] += 1
        else:
            reserve.append(item)
    return tuple(selected), tuple(reserve[:100])
