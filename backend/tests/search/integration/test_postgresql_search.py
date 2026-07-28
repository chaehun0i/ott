from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.catalog.adapters.persistence.models import ActiveProjectionGenerationRow
from ott_feed.search.adapters.persistence.generations import SqlAlchemySearchGenerationRepository
from ott_feed.search.adapters.persistence.models import (
    ContentEmbeddingRow,
    SearchDocumentRow,
)
from ott_feed.search.adapters.persistence.repositories import (
    SqlAlchemyGenerationRegistry,
    SqlAlchemyProjectionRepository,
)
from ott_feed.search.adapters.persistence.vector_repository import SqlAlchemyVectorSearchRepository

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U03 PostgreSQL gate")
    value = create_engine(url, pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


@pytest.fixture
def sessions(engine) -> sessionmaker[Session]:
    with engine.begin() as connection:
        for table in (
            "content_embeddings",
            "search_documents",
            "search_projection_generations",
            "projection_event_receipts",
            "projection_gaps",
            "projection_version_state",
            "active_projection_generations",
        ):
            connection.execute(text(f"DELETE FROM u03_catalog.{table}"))
    return sessionmaker(engine, expire_on_commit=False)


def test_vector_round_trip_hnsw_exact_oracle_and_model_closure(sessions) -> None:
    generation = "g-vector"
    with sessions.begin() as session:
        SqlAlchemySearchGenerationRepository(session).create(generation, 1, "model-v1", 768)
        session.add(
            SearchDocumentRow(
                generation_id=generation,
                content_id="c1",
                locale="ko-KR",
                title="코미디",
                normalized_title="코미디",
                people=[],
                filters={},
                popularity=0.9,
            )
        )
        session.add(
            ContentEmbeddingRow(
                generation_id=generation,
                content_id="c1",
                locale="ko-KR",
                model="model-v1",
                dimension=768,
                embedding=[1.0] + [0.0] * 767,
            )
        )
    with sessions() as session:
        repository = SqlAlchemyVectorSearchRepository(session, model="model-v1", dimension=768)
        query = [1.0] + [0.0] * 767
        assert repository.search(query, generation, 10)[0].content_id == "c1"
        assert repository.exact_oracle(query, generation, 10)[0].content_id == "c1"


def test_receipt_gap_and_atomic_generation_pointer(sessions) -> None:
    event_id = uuid4()
    with sessions.begin() as session:
        projection = SqlAlchemyProjectionRepository(session)
        assert projection.advance("search", 0, 1)
        projection.receipt(event_id, "search", "c1", 1)
        projection.record_gap("search", 2)
    with sessions.begin() as session:
        projection = SqlAlchemyProjectionRepository(session)
        assert projection.has_receipt(event_id, "search")
        assert projection.contiguous_version("search") == 1
        registry = SqlAlchemyGenerationRegistry(session)
        assert registry.compare_and_swap("search", None, "g1")
    with sessions.begin() as session:
        registry = SqlAlchemyGenerationRegistry(session)
        assert not registry.compare_and_swap("search", "wrong", "g2")
        assert registry.active("search") == "g1"
        assert registry.compare_and_swap("search", "g1", "g2")
    with sessions() as session:
        row = session.get(ActiveProjectionGenerationRow, "search")
        assert row is not None and row.previous_generation_id == "g1"


def test_generation_state_compare_and_set(sessions) -> None:
    with sessions.begin() as session:
        repository = SqlAlchemySearchGenerationRepository(session)
        repository.create("quality-g", 1, "model-v1", 768)
        assert repository.set_state("quality-g", "building", "validated")
        assert not repository.set_state("quality-g", "building", "active")
        assert repository.set_state("quality-g", "validated", "active")
