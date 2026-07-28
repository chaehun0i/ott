import os
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ott_feed.platform.adapters.database import OutboxJobRow, SqlAlchemyOutboxRepository
from ott_feed.platform.domain.models import JobStatus, OutboxJob


def test_outbox_enqueue_and_claim_is_transactional() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    OutboxJobRow.__table__.create(engine)
    with Session(engine) as session:
        repository = SqlAlchemyOutboxRepository(session)
        repository.enqueue(OutboxJob("ingestion.refresh", {"provider": "sandbox"}))
        session.commit()

    with Session(engine) as session:
        repository = SqlAlchemyOutboxRepository(session)
        claimed = repository.claim("worker-1", ("ingestion.refresh",), timedelta(seconds=30))
        assert claimed is not None
        assert claimed.status == JobStatus.PROCESSING
        session.commit()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="PostgreSQL test container URL not configured"
)
def test_postgresql_schema_and_atomic_claim() -> None:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    OutboxJobRow.__table__.create(engine, checkfirst=True)
    with Session(engine) as session:
        repository = SqlAlchemyOutboxRepository(session)
        repository.enqueue(OutboxJob("contract.test", {}))
        session.commit()
    with Session(engine) as session:
        claimed = SqlAlchemyOutboxRepository(session).claim(
            "postgres-worker", ("contract.test",), timedelta(seconds=30)
        )
        assert claimed is not None
        session.commit()
