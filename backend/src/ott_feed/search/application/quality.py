"""Bilingual golden-set and exact-vector quality gates."""

from __future__ import annotations

import math
from dataclasses import dataclass


def recall_at_k(actual: list[str], relevant: frozenset[str], k: int = 10) -> float:
    if not relevant:
        return 1.0
    return len(set(actual[:k]) & relevant) / len(relevant)


def ndcg_at_k(actual: list[str], relevant: frozenset[str], k: int = 10) -> float:
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, content_id in enumerate(actual[:k], start=1)
        if content_id in relevant
    )
    ideal_count = min(k, len(relevant))
    if ideal_count == 0:
        return 1.0
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / ideal


@dataclass(frozen=True, slots=True)
class QualityResult:
    recall: float
    ndcg: float
    exact_vector_recall: float
    duplicate_count: int
    closure_failures: int
    smoke_latency_ms: float

    def passes(
        self,
        *,
        recall_threshold: float,
        ndcg_threshold: float,
        latency_threshold_ms: float,
    ) -> bool:
        return (
            self.recall >= recall_threshold
            and self.ndcg >= ndcg_threshold
            and self.exact_vector_recall >= recall_threshold
            and self.duplicate_count == 0
            and self.closure_failures == 0
            and self.smoke_latency_ms <= latency_threshold_ms
        )
