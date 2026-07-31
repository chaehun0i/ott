"""U06 SQLAlchemy unit of work."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from ott_feed.engagement.adapters.persistence.repositories import (
    IncidentRepository,
    NotificationJobRepository,
)


class EngagementUnitOfWork:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    def __enter__(self) -> EngagementUnitOfWork:
        self.session = self.factory()
        self.jobs = NotificationJobRepository(self.session)
        self.incidents = IncidentRepository(self.session)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
