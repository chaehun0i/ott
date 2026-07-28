"""Immutable search generation creation and state persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from ott_feed.search.adapters.persistence.models import SearchProjectionGenerationRow


class SqlAlchemySearchGenerationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, generation_id: str, catalog_version: int, model: str, dimension: int) -> None:
        self.session.add(
            SearchProjectionGenerationRow(
                generation_id=generation_id,
                state="building",
                catalog_version=catalog_version,
                embedding_model=model,
                embedding_dimension=dimension,
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()

    def set_state(self, generation_id: str, expected: str, target: str) -> bool:
        result = cast(
            CursorResult[Any],
            self.session.execute(
                update(SearchProjectionGenerationRow)
                .where(
                    SearchProjectionGenerationRow.generation_id == generation_id,
                    SearchProjectionGenerationRow.state == expected,
                )
                .values(state=target)
            ),
        )
        return bool(result.rowcount == 1)
