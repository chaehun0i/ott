"""Projection receipt, gap and active-generation repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from ott_feed.catalog.adapters.persistence.models import (
    ActiveProjectionGenerationRow,
    ProjectionEventReceiptRow,
    ProjectionGapRow,
    ProjectionVersionStateRow,
)


class SqlAlchemyProjectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def has_receipt(self, event_id: UUID, projection: str) -> bool:
        return self.session.get(ProjectionEventReceiptRow, (event_id, projection)) is not None

    def receipt(self, event_id: UUID, projection: str, content_id: str, version: int) -> None:
        self.session.add(
            ProjectionEventReceiptRow(
                event_id=event_id,
                projection=projection,
                content_id=content_id,
                catalog_version=version,
                applied_at=datetime.now(UTC),
            )
        )

    def contiguous_version(self, projection: str) -> int:
        row = self.session.get(ProjectionVersionStateRow, projection)
        return row.last_contiguous_version if row else 0

    def advance(self, projection: str, expected: int, version: int) -> bool:
        row = self.session.get(ProjectionVersionStateRow, projection)
        if row is None and expected == 0:
            self.session.add(
                ProjectionVersionStateRow(projection=projection, last_contiguous_version=version)
            )
            return True
        result = cast(
            CursorResult[Any],
            self.session.execute(
                update(ProjectionVersionStateRow)
                .where(
                    ProjectionVersionStateRow.projection == projection,
                    ProjectionVersionStateRow.last_contiguous_version == expected,
                )
                .values(last_contiguous_version=version)
            ),
        )
        return result.rowcount == 1

    def record_gap(self, projection: str, missing_version: int) -> None:
        if self.session.get(ProjectionGapRow, (projection, missing_version)) is None:
            self.session.add(
                ProjectionGapRow(
                    projection=projection,
                    missing_version=missing_version,
                    detected_at=datetime.now(UTC),
                )
            )


class SqlAlchemyGenerationRegistry:
    def __init__(self, session: Session) -> None:
        self.session = session

    def active(self, projection: str) -> str | None:
        row = self.session.get(ActiveProjectionGenerationRow, projection)
        return row.generation_id if row else None

    def compare_and_swap(self, projection: str, expected: str | None, candidate: str) -> bool:
        row = self.session.get(ActiveProjectionGenerationRow, projection)
        if row is None:
            if expected is not None:
                return False
            self.session.add(
                ActiveProjectionGenerationRow(
                    projection=projection,
                    generation_id=candidate,
                    previous_generation_id=None,
                    row_version=1,
                )
            )
            return True
        result = cast(
            CursorResult[Any],
            self.session.execute(
                update(ActiveProjectionGenerationRow)
                .where(
                    ActiveProjectionGenerationRow.projection == projection,
                    ActiveProjectionGenerationRow.generation_id == expected,
                )
                .values(
                    previous_generation_id=row.generation_id,
                    generation_id=candidate,
                    row_version=row.row_version + 1,
                )
            ),
        )
        return result.rowcount == 1
