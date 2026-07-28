from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.catalog.adapters.persistence.models import ApprovedContentRow
from ott_feed.catalog.adapters.persistence.unit_of_work import SqlAlchemyCatalogUnitOfWork
from ott_feed.catalog.application.commands import PassedValidationCommand, PublicationAction
from ott_feed.catalog.application.publication import ApprovedCatalogPublicationService
from ott_feed.catalog.domain.models import Availability, CatalogContent, CatalogSource, Localization
from ott_feed.platform.adapters.database import OutboxJobRow

pytestmark = pytest.mark.integration
NOW = datetime(2026, 7, 28, tzinfo=UTC)


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
        connection.execute(text("DELETE FROM u03_catalog.catalog_revisions"))
        connection.execute(text("DELETE FROM u03_catalog.approved_contents"))
        connection.execute(text("DELETE FROM outbox_jobs WHERE job_type LIKE 'u03.%'"))
    return sessionmaker(engine, expire_on_commit=False)


def approved(content_id: str = "catalog-integration") -> CatalogContent:
    return CatalogContent(
        id=content_id,
        content_type="movie",
        genres=frozenset({"comedy"}),
        release_at=NOW,
        runtime_minutes=60,
        popularity=0.8,
        localizations={"ko-KR": Localization("ko-KR", "통합 영화", "요약")},
        availability=(
            Availability(
                "KR",
                "netflix",
                NOW,
                NOW - timedelta(days=1),
                detail_url="https://example.test/detail",
            ),
        ),
        source=CatalogSource("provider", "source-1", "license-1", NOW),
    )


def test_u03_schema_extensions_and_migration_head(engine) -> None:
    with engine.connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        extensions = set(
            connection.scalars(
                text(
                    "SELECT extname FROM pg_extension "
                    "WHERE extname IN ('pg_trgm','unaccent','vector')"
                )
            )
        )
        tables = connection.scalar(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema='u03_catalog'")
        )
    assert revision == "0003_u03_catalog_expand"
    assert extensions == {"pg_trgm", "unaccent", "vector"}
    assert tables == 15


def test_publication_withdrawal_and_outbox_are_atomic(sessions) -> None:
    service = ApprovedCatalogPublicationService(
        lambda: SqlAlchemyCatalogUnitOfWork(sessions, statement_timeout_ms=3000)
    )
    command = PassedValidationCommand(
        PublicationAction.PUBLISH, "catalog-integration", "decision-publish", approved()
    )
    assert service.execute(command).value == 1
    assert service.execute(command).value == 1
    assert (
        service.execute(
            PassedValidationCommand(
                PublicationAction.WITHDRAW, "catalog-integration", "decision-withdraw"
            )
        ).value
        == 2
    )
    with sessions() as session:
        row = session.get(ApprovedContentRow, "catalog-integration")
        jobs = session.scalars(
            select(OutboxJobRow).where(OutboxJobRow.job_type == "u03.catalog.versioned")
        ).all()
        assert row is not None and row.state == "withdrawn"
        assert len(jobs) == 2 and jobs[-1].lane == "high"


def test_transaction_rollback_does_not_leave_catalog_or_outbox(sessions) -> None:
    with pytest.raises(RuntimeError), SqlAlchemyCatalogUnitOfWork(sessions) as uow:
        value = approved("rollback-content")
        value.last_decision_id = "decision-rollback"
        uow.catalog.save(value, None)
        raise RuntimeError("failure injection")
    with sessions() as session:
        assert session.get(ApprovedContentRow, "rollback-content") is None
