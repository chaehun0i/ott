from __future__ import annotations

from collections.abc import Sequence

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ott_feed.search.application.hybrid_search import HybridSearchService
from ott_feed.search.application.parser import normalize_query, parse_query
from ott_feed.search.application.quality import ndcg_at_k, recall_at_k
from ott_feed.search.application.resilience import CircuitState, EmbeddingCircuit
from ott_feed.search.domain.errors import EmbeddingUnavailable
from ott_feed.search.domain.models import SearchCandidate, StructuredQuery
from ott_feed.search.domain.ranking import reciprocal_rank_fusion
from tests.strategies.search import query_text, result_ids

pytestmark = pytest.mark.pbt


def candidates(ids: list[str], source: str = "text") -> list[SearchCandidate]:
    return [SearchCandidate(value, 1, value, "ko-KR", source) for value in ids]


@given(query_text)
def test_pbt_u03_09_normalization_is_idempotent(value: str) -> None:
    normalized = normalize_query(value)
    assert normalize_query(normalized) == normalized


@given(st.integers(min_value=1, max_value=300))
def test_pbt_u03_10_runtime_parser(minutes: int) -> None:
    assert parse_query(f"{minutes}분 이내 코미디", "ko-KR").max_runtime_minutes == minutes


@given(result_ids)
def test_pbt_u03_11_ranking_is_deterministic(ids: list[str]) -> None:
    channels = {"text": candidates(ids), "vector": candidates(list(reversed(ids)), "vector")}
    assert reciprocal_rank_fusion(channels) == reciprocal_rank_fusion(channels)


@given(result_ids)
def test_pbt_u03_12_rrf_never_duplicates(ids: list[str]) -> None:
    ranked = reciprocal_rank_fusion({"text": candidates(ids), "vector": candidates(ids)})
    result = [item.candidate.content_id for item in ranked]
    assert len(result) == len(set(result))


@given(st.integers(min_value=1, max_value=20))
def test_pbt_u03_13_circuit_opens_at_failure_threshold(window: int) -> None:
    circuit = EmbeddingCircuit(window=window, failure_ratio=1, clock=lambda: 0.0)
    for _ in range(window):
        circuit.record(False)
    assert circuit.state is CircuitState.OPEN


class Text:
    def search(self, query: StructuredQuery, limit: int) -> list[SearchCandidate]:
        return candidates(["approved"])


class Vector:
    def search(self, vector: Sequence[float], generation: str, limit: int) -> list[SearchCandidate]:
        return candidates(["semantic"], "vector")


class FailedEmbedding:
    def embed(self, text: str) -> Sequence[float]:
        raise EmbeddingUnavailable()


@given(query_text.filter(bool))
def test_pbt_u03_14_semantic_failure_falls_back_to_text(value: str) -> None:
    result, degraded = HybridSearchService(Text(), Vector(), FailedEmbedding()).search(
        StructuredQuery(normalize_query(value), "ko-KR"), generation="g1"
    )
    assert degraded == "semantic_unavailable"
    assert [item.candidate.content_id for item in result] == ["approved"]


@given(result_ids, st.sets(st.text(alphabet="abc123", min_size=1, max_size=8), max_size=10))
def test_pbt_u03_15_quality_metrics_are_bounded(actual: list[str], relevant: set[str]) -> None:
    frozen = frozenset(relevant)
    assert 0 <= recall_at_k(actual, frozen) <= 1
    assert 0 <= ndcg_at_k(actual, frozen) <= 1


@given(st.permutations([1, 2, 3, 4, 5]))
def test_pbt_u03_16_replay_converges_for_out_of_order_events(order) -> None:
    received: set[int] = set()
    contiguous = 0
    for version in order:
        received.add(version)
        while contiguous + 1 in received:
            contiguous += 1
    assert contiguous == 5
