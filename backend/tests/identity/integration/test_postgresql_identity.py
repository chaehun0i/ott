from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.identity.adapters.export_storage import (
    EncryptedExportStorage,
    InMemoryPrivateObjectClient,
)
from ott_feed.identity.adapters.persistence.feature_repository import (
    SqlAlchemyFeatureRepository,
)
from ott_feed.identity.adapters.persistence.models import UserRow
from ott_feed.identity.adapters.persistence.repositories import (
    SqlAlchemyDataRightsRepository,
    SqlAlchemyIdentityRepository,
)
from ott_feed.identity.adapters.persistence.unit_of_work import SqlAlchemyIdentityUnitOfWork
from ott_feed.identity.domain.errors import IdentityError
from ott_feed.identity.domain.models import (
    DataRightsRequest,
    DataRightsStatus,
    DataRightsType,
    FeatureContribution,
    OAuthLink,
    Role,
    User,
    UserStatus,
)
from ott_feed.platform.adapters.database import OutboxJobRow

pytestmark = pytest.mark.integration
NOW = datetime(2026, 7, 27, tzinfo=UTC)


@pytest.fixture(scope="module")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.fail("TEST_DATABASE_URL is mandatory for the U02 PostgreSQL gate")
    created = create_engine(url, pool_pre_ping=True)
    try:
        yield created
    finally:
        created.dispose()


@pytest.fixture(scope="module")
def sessions(engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def new_user(*, subject: bytes | None = None) -> User:
    user = User(
        {"ciphertext": "opaque"},
        1,
        uuid4().bytes + uuid4().bytes,
        status=UserStatus.ACTIVE,
        roles={Role.MEMBER},
        created_at=NOW,
        updated_at=NOW,
    )
    if subject is not None:
        user.oauth_links.append(OAuthLink("google", subject, None, linked_at=NOW))
    return user


def persist_user(sessions: sessionmaker[Session], user: User) -> None:
    with sessions.begin() as session:
        SqlAlchemyIdentityRepository(session).save_user(user)


def test_postgresql_17_10_migration_and_u02_schema_are_current(engine) -> None:
    with engine.connect() as connection:
        version = connection.scalar(text("show server_version"))
        revision = connection.scalar(text("select version_num from alembic_version"))
        table_count = connection.scalar(
            text(
                "select count(*) from information_schema.tables where table_schema = 'u02_identity'"
            )
        )

    # Distribution images can append build metadata (for example Debian package details).
    assert version.startswith("17.10")
    assert revision is not None and int(revision[:4]) >= 2
    assert table_count == 23


def test_unique_google_subject_and_optimistic_user_conflict(
    sessions: sessionmaker[Session],
) -> None:
    subject = uuid4().bytes + uuid4().bytes
    first = new_user(subject=subject)
    persist_user(sessions, first)

    second = new_user(subject=subject)
    with (
        pytest.raises(IdentityError, match="persistence_unique_conflict"),
        sessions.begin() as session,
    ):
        SqlAlchemyIdentityRepository(session).save_user(second)

    with sessions() as left_session, sessions() as right_session:
        left_repo = SqlAlchemyIdentityRepository(left_session)
        right_repo = SqlAlchemyIdentityRepository(right_session)
        left = left_repo.get_user(first.id)
        right = right_repo.get_user(first.id)
        assert left is not None and right is not None
        left_expected = left.row_version
        left.grant_role(Role.CONTENT_OPERATOR, NOW)
        left_repo.save_user(left, left_expected)
        left_session.commit()
        right_expected = right.row_version
        right.updated_at = NOW + timedelta(seconds=1)
        right.row_version += 1
        with pytest.raises(IdentityError, match="optimistic_conflict"):
            right_repo.save_user(right, right_expected)
        right_session.rollback()


def test_uow_rolls_back_identity_and_outbox_then_persists_high_lane_atomically(
    sessions: sessionmaker[Session],
) -> None:
    rolled_back = new_user()
    job_id: UUID | None = None
    with (
        pytest.raises(RuntimeError, match="inject rollback"),
        SqlAlchemyIdentityUnitOfWork(sessions) as work,
    ):
        work.identities.save_user(rolled_back)
        job_id = work.jobs.enqueue(
            "identity.data-rights.deletion", {"userId": str(rolled_back.id)}, "high"
        )
        raise RuntimeError("inject rollback")

    assert job_id is not None
    with sessions() as session:
        assert session.get(UserRow, rolled_back.id) is None
        assert session.get(OutboxJobRow, job_id) is None

    committed = new_user()
    with SqlAlchemyIdentityUnitOfWork(sessions) as work:
        work.identities.save_user(committed)
        committed_job = work.jobs.enqueue(
            "identity.data-rights.deletion", {"userId": str(committed.id)}, "high"
        )
        work.commit()
    with sessions() as session:
        row = session.get(OutboxJobRow, committed_job)
        assert row is not None
        assert row.lane == "high"
        assert row.priority == 0


def test_feature_cas_orders_versions_and_deduplicates_contributions(
    sessions: sessionmaker[Session],
) -> None:
    user = new_user()
    persist_user(sessions, user)
    consent_id = uuid4()
    contribution = FeatureContribution(uuid4(), "behavior:click", 1.0, consent_id)

    with sessions.begin() as session:
        repository = SqlAlchemyFeatureRepository(session)
        feature_set, created = repository.apply_contribution(user.id, 1, contribution, 1)
        assert created is True
        assert feature_set.feature_version == 2

    with sessions.begin() as session:
        repository = SqlAlchemyFeatureRepository(session)
        feature_set, created = repository.apply_contribution(user.id, 1, contribution, 2)
        assert created is False
        assert feature_set.feature_version == 2
        with pytest.raises(IdentityError, match="feature_version_conflict"):
            repository.replace_explicit(user.id, {"genre:comedy": 1.0}, 1, 1)


def test_data_rights_retry_state_and_encrypted_export_single_use(
    sessions: sessionmaker[Session],
) -> None:
    user = new_user()
    persist_user(sessions, user)
    request = DataRightsRequest(user.id, DataRightsType.DELETION, f"delete-{uuid4()}")
    request.authorize(NOW)
    request.start()
    first_step = next(iter(request.deletion_steps.values()))
    first_step.start()
    first_step.fail("InjectedFailure")
    request.complete()
    assert request.status == DataRightsStatus.PARTIALLY_COMPLETED

    with sessions.begin() as session:
        SqlAlchemyDataRightsRepository(session).save(request)
    with sessions.begin() as session:
        restored = SqlAlchemyDataRightsRepository(session).get(request.id)
        assert restored is not None
        assert restored.status == DataRightsStatus.PARTIALLY_COMPLETED
        assert restored.deletion_steps[first_step.category].failure_code == "InjectedFailure"

    client = InMemoryPrivateObjectClient()
    storage = EncryptedExportStorage(client, b"integration-export-key")
    reference = storage.put_encrypted("exports/one", b"private-export", NOW + timedelta(hours=1))
    assert storage.get_once(reference) == b"private-export"
    with pytest.raises(IdentityError, match="export_not_found"):
        storage.get_once(reference)


def test_database_contains_no_duplicate_active_google_subject(
    sessions: sessionmaker[Session],
) -> None:
    with sessions() as session:
        duplicate_count = session.scalar(
            text(
                "select count(*) from (select provider, provider_subject_index "
                "from u02_identity.oauth_links where revoked_at is null "
                "group by provider, provider_subject_index having count(*) > 1) duplicates"
            )
        )
    assert duplicate_count == 0
