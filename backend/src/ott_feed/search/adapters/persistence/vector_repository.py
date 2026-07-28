"""Compatible-generation pgvector HNSW and exact oracle retrieval."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ott_feed.search.adapters.persistence.models import (
    ContentEmbeddingRow,
    SearchDocumentRow,
    SearchProjectionGenerationRow,
)
from ott_feed.search.domain.models import SearchCandidate


class SqlAlchemyVectorSearchRepository:
    def __init__(self, session: Session, *, model: str, dimension: int) -> None:
        self.session = session
        self.model = model
        self.dimension = dimension

    def search(self, vector: Sequence[float], generation: str, limit: int) -> list[SearchCandidate]:
        if len(vector) != self.dimension:
            raise ValueError("query embedding dimension mismatch")
        distance = ContentEmbeddingRow.embedding.cosine_distance(list(vector))
        statement = (
            select(ContentEmbeddingRow, SearchDocumentRow, distance.label("distance"))
            .join(
                SearchProjectionGenerationRow,
                SearchProjectionGenerationRow.generation_id == ContentEmbeddingRow.generation_id,
            )
            .join(
                SearchDocumentRow,
                (SearchDocumentRow.generation_id == ContentEmbeddingRow.generation_id)
                & (SearchDocumentRow.content_id == ContentEmbeddingRow.content_id)
                & (SearchDocumentRow.locale == ContentEmbeddingRow.locale),
            )
            .where(
                ContentEmbeddingRow.generation_id == generation,
                ContentEmbeddingRow.model == self.model,
                ContentEmbeddingRow.dimension == self.dimension,
                SearchProjectionGenerationRow.embedding_model == self.model,
                SearchProjectionGenerationRow.embedding_dimension == self.dimension,
            )
            .order_by(distance, ContentEmbeddingRow.content_id)
            .limit(limit)
        )
        return [
            SearchCandidate(
                content_id=document.content_id,
                score=1.0 - float(distance_value),
                title=document.title,
                actual_locale=document.locale,
                source="vector",
            )
            for _, document, distance_value in self.session.execute(statement).all()
        ]

    def exact_oracle(
        self, vector: Sequence[float], generation: str, limit: int
    ) -> list[SearchCandidate]:
        self.session.execute(text("SET LOCAL enable_indexscan = off"))
        return self.search(vector, generation, limit)
