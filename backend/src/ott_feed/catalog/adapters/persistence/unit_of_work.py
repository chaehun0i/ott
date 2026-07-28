"""Separate API/worker transaction profiles for U03."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.catalog.adapters.persistence.repositories import SqlAlchemyCatalogRepository
from ott_feed.platform.adapters.database import SqlAlchemyOutboxRepository


class SqlAlchemyCatalogUnitOfWork:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        statement_timeout_ms: int = 1500,
    ) -> None:
        self.sessions = sessions
        self.statement_timeout_ms = statement_timeout_ms
        self.session: Session | None = None
        self.catalog: SqlAlchemyCatalogRepository
        self.outbox: SqlAlchemyOutboxRepository

    def __enter__(self) -> SqlAlchemyCatalogUnitOfWork:
        self.session = self.sessions()
        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            self.session.execute(
                text("SELECT set_config('statement_timeout', :timeout, true)"),
                {"timeout": f"{self.statement_timeout_ms}ms"},
            )
        self.catalog = SqlAlchemyCatalogRepository(self.session)
        self.outbox = SqlAlchemyOutboxRepository(self.session)
        return self

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work has not started")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.rollback()
        if self.session is not None:
            self.session.close()
