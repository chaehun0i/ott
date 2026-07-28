"""U04 API/worker transaction boundary with PostgreSQL statement budgets."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from ott_feed.ingestion.adapters.persistence.models import (
    MergedMetadataRow,
    NormalizedMetadataRow,
    ProviderPolicyRow,
    PublicationReceiptRow,
    QuarantineRow,
    ValidationDecisionRow,
)
from ott_feed.ingestion.adapters.persistence.repositories import (
    IngestionRepositories,
    JobRepository,
    RawRecordRepository,
    RowRepository,
)


class SqlAlchemyIngestionUnitOfWork:
    def __init__(
        self, sessions: sessionmaker[Session], *, statement_timeout_ms: int = 5_000
    ) -> None:
        if statement_timeout_ms <= 0:
            raise ValueError("statement timeout must be positive")
        self.sessions = sessions
        self.statement_timeout_ms = statement_timeout_ms
        self.session: Session | None = None
        self.repositories: IngestionRepositories

    def __enter__(self) -> SqlAlchemyIngestionUnitOfWork:
        self.session = self.sessions()
        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            self.session.execute(
                text("SELECT set_config('statement_timeout', :timeout, true)"),
                {"timeout": f"{self.statement_timeout_ms}ms"},
            )
        self.repositories = IngestionRepositories(self.session)
        return self

    @property
    def jobs(self) -> JobRepository:
        return self.repositories.jobs

    @property
    def policies(self) -> RowRepository[ProviderPolicyRow]:
        return self.repositories.policies

    @property
    def raw_records(self) -> RawRecordRepository:
        return self.repositories.raw_records

    @property
    def normalized(self) -> RowRepository[NormalizedMetadataRow]:
        return self.repositories.normalized

    @property
    def merges(self) -> RowRepository[MergedMetadataRow]:
        return self.repositories.merges

    @property
    def validations(self) -> RowRepository[ValidationDecisionRow]:
        return self.repositories.validations

    @property
    def quarantine(self) -> RowRepository[QuarantineRow]:
        return self.repositories.quarantine

    @property
    def publications(self) -> RowRepository[PublicationReceiptRow]:
        return self.repositories.publications

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
