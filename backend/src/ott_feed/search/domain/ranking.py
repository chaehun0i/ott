"""Versioned reciprocal-rank fusion with exact-title priority."""

from __future__ import annotations

from collections import defaultdict

from ott_feed.search.domain.models import RankedResult, SearchCandidate


def reciprocal_rank_fusion(
    channels: dict[str, list[SearchCandidate]], *, k: int = 60, limit: int = 20
) -> list[RankedResult]:
    if k <= 0 or limit <= 0:
        raise ValueError("RRF k and limit must be positive")
    scores: dict[str, float] = defaultdict(float)
    candidates: dict[str, SearchCandidate] = {}
    memberships: dict[str, set[str]] = defaultdict(set)
    exact_ids: set[str] = set()
    for channel, values in sorted(channels.items()):
        for rank, candidate in enumerate(values, start=1):
            scores[candidate.content_id] += 1 / (k + rank)
            candidates.setdefault(candidate.content_id, candidate)
            memberships[candidate.content_id].add(channel)
            if channel == "exact":
                exact_ids.add(candidate.content_id)
    ordered = sorted(
        candidates,
        key=lambda content_id: (
            content_id not in exact_ids,
            -scores[content_id],
            content_id,
        ),
    )[:limit]
    return [
        RankedResult(candidates[content_id], rank, tuple(sorted(memberships[content_id])))
        for rank, content_id in enumerate(ordered, start=1)
    ]
