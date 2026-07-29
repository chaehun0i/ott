import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from ott_feed.recommendation.adapters.persistence.models import RecommendationSessionRow
from ott_feed.recommendation.adapters.persistence.repositories import SessionRepository
from ott_feed.recommendation.domain.errors import RecommendationError

pytestmark = pytest.mark.integration


def database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U05 PostgreSQL gate")
    return url


def test_u05_schema_and_optimistic_session_closure() -> None:
    engine = create_engine(database_url())
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.query(RecommendationSessionRow).filter_by(session_id="u05-integration").delete()
        session.add(
            RecommendationSessionRow(
                session_id="u05-integration",
                owner_id="subject",
                epoch=0,
                version=0,
                intent={},
                idempotency_key=None,
                updated_at=now,
            )
        )
        session.commit()
    with Session(engine) as session:
        row = session.scalar(
            select(RecommendationSessionRow).where(
                RecommendationSessionRow.session_id == "u05-integration"
            )
        )
        assert row is not None
        row.version = 1
        row.idempotency_key = "u05-key-1"
        SessionRepository(session).save(row, expected_version=0)
        session.commit()
    with Session(engine) as session:
        stale = RecommendationSessionRow(
            session_id="u05-integration",
            owner_id="subject",
            epoch=0,
            version=2,
            intent={},
            idempotency_key="u05-key-2",
            updated_at=now,
        )
        with pytest.raises(RecommendationError, match="version conflict"):
            SessionRepository(session).save(stale, expected_version=0)
        session.rollback()
