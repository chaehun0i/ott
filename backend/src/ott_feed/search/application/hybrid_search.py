"""Hybrid search with approved text fallback for semantic failures."""

from __future__ import annotations

from ott_feed.search.domain.errors import EmbeddingUnavailable
from ott_feed.search.domain.models import RankedResult, StructuredQuery
from ott_feed.search.domain.ranking import reciprocal_rank_fusion
from ott_feed.search.ports import EmbeddingPort, TextSearchPort, VectorSearchPort


class HybridSearchService:
    def __init__(
        self,
        text: TextSearchPort,
        vector: VectorSearchPort,
        embedding: EmbeddingPort,
        *,
        rrf_k: int = 60,
    ) -> None:
        self.text = text
        self.vector = vector
        self.embedding = embedding
        self.rrf_k = rrf_k

    def search(
        self, query: StructuredQuery, *, generation: str, limit: int = 20
    ) -> tuple[list[RankedResult], str | None]:
        text_results = self.text.search(query, limit * 2)
        exact = [item for item in text_results if item.title.casefold() == query.text]
        channels = {"exact": exact, "text": text_results}
        degraded_reason: str | None = None
        try:
            embedding = self.embedding.embed(query.text)
            channels["vector"] = self.vector.search(embedding, generation, limit * 2)
        except (EmbeddingUnavailable, TimeoutError, ValueError):
            degraded_reason = "semantic_unavailable"
        return reciprocal_rank_fusion(channels, k=self.rrf_k, limit=limit), degraded_reason
