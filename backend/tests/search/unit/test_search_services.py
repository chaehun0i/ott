from __future__ import annotations

from collections.abc import Sequence

import httpx
import pytest

from ott_feed.search.adapters.embedding import HttpEmbeddingAdapter
from ott_feed.search.adapters.security import CursorSigner
from ott_feed.search.application.hybrid_search import HybridSearchService
from ott_feed.search.application.parser import normalize_query, parse_query
from ott_feed.search.application.quality import QualityResult, ndcg_at_k, recall_at_k
from ott_feed.search.application.rebuild import OnlineRebuildService
from ott_feed.search.application.resilience import CircuitState, EmbeddingCircuit
from ott_feed.search.config import SearchSettings
from ott_feed.search.domain.errors import CursorError, EmbeddingUnavailable
from ott_feed.search.domain.models import SearchCandidate, StructuredQuery
from ott_feed.search.domain.ranking import reciprocal_rank_fusion


def candidate(content_id: str, title: str, source: str = "text") -> SearchCandidate:
    return SearchCandidate(content_id, 1.0, title, "ko-KR", source)


class TextRepo:
    def search(self, query: StructuredQuery, limit: int) -> list[SearchCandidate]:
        return [candidate("exact", query.text), candidate("text", "other")][:limit]


class VectorRepo:
    def search(self, vector: Sequence[float], generation: str, limit: int) -> list[SearchCandidate]:
        return [candidate("vector", "semantic", "vector")][:limit]


class Embedder:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def embed(self, text: str) -> Sequence[float]:
        if self.fail:
            raise EmbeddingUnavailable()
        return [1.0, 0.0]


class Telemetry:
    def __init__(self) -> None:
        self.reasons: list[str | None] = []

    def result(self, *, degraded_reason: str | None, result_count: int) -> None:
        self.reasons.append(degraded_reason)


def test_parser_ranking_hybrid_and_fallback() -> None:
    query = parse_query("  퇴근 후 1시간 이내 코미디  ", "ko-KR")
    assert query.max_runtime_minutes == 60 and query.genres == {"comedy"}
    assert normalize_query("Ａ  B") == "a b"
    ranked = reciprocal_rank_fusion(
        {"text": [candidate("b", "B")], "exact": [candidate("a", "A")]}, k=60
    )
    assert [item.candidate.content_id for item in ranked] == ["a", "b"]
    service = HybridSearchService(TextRepo(), VectorRepo(), Embedder())
    result, degraded = service.search(StructuredQuery("exact", "ko-KR"), generation="g1")
    assert degraded is None and {item.candidate.content_id for item in result} == {
        "exact",
        "text",
        "vector",
    }
    _, degraded = HybridSearchService(TextRepo(), VectorRepo(), Embedder(True)).search(
        StructuredQuery("exact", "ko-KR"), generation="g1"
    )
    assert degraded == "semantic_unavailable"


def test_cursor_round_trip_rotation_and_tamper() -> None:
    from ott_feed.catalog.domain.models import FeedCursor

    old = CursorSigner(b"o" * 32)
    token = old.encode(FeedCursor("fp", "g1", 0.5, "c1"))
    rotated = CursorSigner(b"n" * 32, b"o" * 32)
    assert rotated.decode(token).content_id == "c1"
    assert rotated.fingerprint("same") == rotated.fingerprint("same")
    with pytest.raises(CursorError):
        rotated.decode(token[:-2] + "xx")


def test_embedding_adapter_contract_and_circuit() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"model": "m1", "embedding": [1, 0]}, request=request
        )
    )
    client = httpx.Client(transport=transport)
    adapter = HttpEmbeddingAdapter(
        url="https://embedding.test/v1",
        model="m1",
        dimension=2,
        allowed_hosts=frozenset({"embedding.test"}),
        client=client,
    )
    assert list(adapter.embed("hello")) == [1.0, 0.0]
    with pytest.raises(ValueError):
        HttpEmbeddingAdapter(
            url="https://evil.test/v1",
            model="m1",
            dimension=2,
            allowed_hosts=frozenset({"embedding.test"}),
        )
    circuit = EmbeddingCircuit(window=2, failure_ratio=0.5, clock=lambda: 0.0)
    circuit.record(False)
    circuit.record(True)
    assert circuit.state is CircuitState.OPEN
    with pytest.raises(EmbeddingUnavailable):
        circuit.before_call()


def test_quality_rebuild_and_settings() -> None:
    assert recall_at_k(["a", "x"], frozenset({"a", "b"})) == 0.5
    assert 0 < ndcg_at_k(["a", "x"], frozenset({"a", "b"})) < 1
    quality = QualityResult(0.9, 0.9, 0.9, 0, 0, 100)
    telemetry = Telemetry()
    active = {"search": "old"}

    def swap(projection: str, expected: str | None, candidate_id: str) -> bool:
        if active.get(projection) != expected:
            return False
        active[projection] = candidate_id
        return True

    service = OnlineRebuildService(
        active=lambda projection: active.get(projection),
        compare_and_swap=swap,
        build=lambda candidate_id: None,
        validate=lambda candidate_id: quality,
        telemetry=telemetry,
    )
    result = service.run("search", "new", online_slo_healthy=True)
    assert result.activated and active["search"] == "new"
    assert not service.run("search", "next", online_slo_healthy=False).activated
    with pytest.raises(ValueError):
        SearchSettings(embedding_dimension=0)
