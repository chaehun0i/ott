"""U05 transaction boundary."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from ott_feed.recommendation.adapters.persistence.repositories import (
    ROW_TYPES,
    RowRepository,
    SessionRepository,
    TraceRepository,
)


class SQLAlchemyRecommendationUnitOfWork:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory
        self.session: Session | None = None

    def __enter__(self) -> SQLAlchemyRecommendationUnitOfWork:
        self.session = self.factory()
        self.sessions = SessionRepository(self.session)
        self.requests = RowRepository(self.session, ROW_TYPES["requests"])
        self.policies = RowRepository(self.session, ROW_TYPES["policies"])
        self.rankings = RowRepository(self.session, ROW_TYPES["rankings"])
        self.validations = RowRepository(self.session, ROW_TYPES["validations"])
        self.traces = TraceRepository(self.session, ROW_TYPES["traces"])
        self.usage = RowRepository(self.session, ROW_TYPES["usage"])
        self.retention = RowRepository(self.session, ROW_TYPES["retention"])
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None:
        if self.session is not None:
            if exc_type is not None:
                self.session.rollback()
            self.session.close()
        return None

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()
