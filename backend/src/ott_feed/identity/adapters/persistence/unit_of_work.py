"""Request-scoped SQLAlchemy transaction boundary for U02."""

from __future__ import annotations

from sqlalchemy.orm import Session as SqlSession
from sqlalchemy.orm import sessionmaker

from ott_feed.identity.adapters.persistence.feature_repository import (
    SqlAlchemyFeatureRepository,
)
from ott_feed.identity.adapters.persistence.repositories import (
    SqlAlchemyBehaviorRepository,
    SqlAlchemyConsentRepository,
    SqlAlchemyDataRightsRepository,
    SqlAlchemyIdentityRepository,
    SqlAlchemyJobPublisher,
    SqlAlchemyLibraryRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySessionRepository,
)


class SqlAlchemyIdentityUnitOfWork:
    def __init__(self, factory: sessionmaker[SqlSession]) -> None:
        self._factory = factory
        self.session: SqlSession | None = None

    def __enter__(self) -> SqlAlchemyIdentityUnitOfWork:
        self.session = self._factory()
        self.identities = SqlAlchemyIdentityRepository(self.session)
        self.sessions = SqlAlchemySessionRepository(self.session)
        self.profiles = SqlAlchemyProfileRepository(self.session)
        self.libraries = SqlAlchemyLibraryRepository(self.session)
        self.consents = SqlAlchemyConsentRepository(self.session)
        self.behavior = SqlAlchemyBehaviorRepository(self.session)
        self.features = SqlAlchemyFeatureRepository(self.session)
        self.data_rights = SqlAlchemyDataRightsRepository(self.session)
        self.jobs = SqlAlchemyJobPublisher(self.session)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.session is None:
            return
        try:
            if exc_type is not None:
                self.session.rollback()
        finally:
            self.session.close()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        self.session.rollback()
