from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.ingestion.adapters.persistence.models import IngestionJobRow, ProviderPolicyRow
from ott_feed.ingestion.adapters.persistence.unit_of_work import SqlAlchemyIngestionUnitOfWork
from ott_feed.ingestion.domain.errors import IngestionError

pytestmark = pytest.mark.integration
NOW = datetime(2026, 7, 28, tzinfo=UTC)


@pytest.fixture(scope="module")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U04 PostgreSQL gate")
    value = create_engine(url, pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


@pytest.fixture
def sessions(engine) -> sessionmaker[Session]:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE u04_ingestion.provider_policies CASCADE"))
    return sessionmaker(engine, expire_on_commit=False)


def add_job(sessions: sessionmaker[Session], job_id: str = "job-1") -> None:
    with sessions() as session:
        session.add(
            ProviderPolicyRow(
                policy_id="policy-1",
                provider_id="provider-1",
                version=1,
                status="active",
                policy={"allowed_uses": ["collect"]},
                effective_from=NOW,
            )
        )
        session.flush()
        session.add(
            IngestionJobRow(
                job_id=job_id,
                provider_id="provider-1",
                policy_id="policy-1",
                lane="u04_incremental",
                priority=100,
                status="scheduled",
                claim_version=0,
                available_at=NOW,
                summary={},
                created_at=NOW,
            )
        )
        session.commit()


def test_u04_schema_and_migration_head(engine) -> None:
    with engine.connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        tables = connection.scalar(
            text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='u04_ingestion'"
            )
        )
    assert revision == "0004_u04_ingestion_expand"
    assert tables == 13


def test_claim_is_bounded_and_fenced(sessions) -> None:
    add_job(sessions)
    with SqlAlchemyIngestionUnitOfWork(sessions) as first:
        claimed = first.jobs.claim("worker-1", ("u04_incremental",), 30, now=NOW)
        assert claimed is not None and claimed.claim_version == 1
        with SqlAlchemyIngestionUnitOfWork(sessions) as concurrent:
            assert concurrent.jobs.claim("worker-2", ("u04_incremental",), 30, now=NOW) is None
        first.commit()
    with SqlAlchemyIngestionUnitOfWork(sessions) as second:
        with pytest.raises(IngestionError, match="no longer current"):
            second.jobs.advance_cursor("job-1", 0, "cursor-1", {"succeeded": 1})


def test_expired_lease_can_be_reclaimed(sessions) -> None:
    add_job(sessions, "job-expired")
    with sessions() as session:
        row = session.get(IngestionJobRow, "job-expired")
        assert row is not None
        row.status = "retry_pending"
        row.lease_until = NOW - timedelta(seconds=1)
        session.commit()
    with SqlAlchemyIngestionUnitOfWork(sessions) as uow:
        claimed = uow.jobs.claim("worker-2", ("u04_incremental",), 30, now=NOW)
        assert claimed is not None and claimed.job_id == "job-expired"
        assert claimed.claim_version == 1
        uow.commit()


def test_unit_of_work_rolls_back(sessions) -> None:
    with pytest.raises(RuntimeError), SqlAlchemyIngestionUnitOfWork(sessions) as uow:
        uow.policies.add(
            ProviderPolicyRow(
                policy_id="rollback-policy",
                provider_id="provider-r",
                version=1,
                status="active",
                policy={},
                effective_from=NOW,
            )
        )
        raise RuntimeError("failure injection")
    with sessions() as session:
        assert session.get(ProviderPolicyRow, "rollback-policy") is None
