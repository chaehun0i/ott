"""Catalog repositories with compare-and-set writes and typed translation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ott_feed.catalog.adapters.persistence.models import (
    ApprovedContentRow,
    CatalogRevisionRow,
    CatalogSourceRow,
    ContentAvailabilityRow,
    ContentLocalizationRow,
)
from ott_feed.catalog.domain.errors import CatalogConflict, CatalogError
from ott_feed.catalog.domain.models import (
    Availability,
    CatalogContent,
    CatalogSource,
    CatalogState,
    CatalogVersion,
    Localization,
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, content_id: str) -> CatalogContent | None:
        row = self.session.get(ApprovedContentRow, content_id)
        if row is None:
            return None
        localizations = self.session.scalars(
            select(ContentLocalizationRow).where(ContentLocalizationRow.content_id == content_id)
        ).all()
        sources = self.session.scalars(
            select(CatalogSourceRow).where(CatalogSourceRow.content_id == content_id)
        ).all()
        availability = self.session.scalars(
            select(ContentAvailabilityRow).where(ContentAvailabilityRow.content_id == content_id)
        ).all()
        if not sources:
            raise CatalogError("CAT_SOURCE_MISSING", "approved content has no source")
        source = sources[0]
        return CatalogContent(
            id=row.content_id,
            content_type=row.content_type,
            genres=frozenset(row.genres),
            release_at=_aware(row.release_at),
            runtime_minutes=row.runtime_minutes,
            popularity=row.popularity,
            localizations={
                item.locale: Localization(
                    item.locale, item.title, item.synopsis, tuple(item.people)
                )
                for item in localizations
            },
            availability=tuple(
                Availability(
                    item.region,
                    item.provider,
                    _aware(item.verified_at),
                    _aware(item.starts_at),
                    _aware(item.ends_at) if item.ends_at else None,
                    item.direct_url,
                    item.detail_url,
                )
                for item in availability
                if item.verified
            ),
            source=CatalogSource(
                source.provider,
                source.source_record_id,
                source.license_reference,
                _aware(source.last_success_at),
            ),
            state=CatalogState(row.state),
            version=CatalogVersion(row.catalog_version),
            revision=row.current_revision,
            last_decision_id=row.current_decision_id,
        )

    def save(self, content: CatalogContent, expected_version: CatalogVersion | None) -> None:
        try:
            existing = self.session.get(ApprovedContentRow, content.id)
            if existing is None:
                if expected_version is not None:
                    raise CatalogConflict()
                self.session.add(self._new_row(content))
            else:
                if expected_version is None:
                    raise CatalogConflict()
                result = cast(
                    CursorResult[Any],
                    self.session.execute(
                        update(ApprovedContentRow)
                        .where(
                            ApprovedContentRow.content_id == content.id,
                            ApprovedContentRow.catalog_version == expected_version.value,
                        )
                        .values(
                            content_type=content.content_type,
                            state=content.state.value,
                            current_revision=content.revision,
                            catalog_version=content.version.value,
                            release_at=content.release_at,
                            runtime_minutes=content.runtime_minutes,
                            popularity=content.popularity,
                            genres=sorted(content.genres),
                            current_decision_id=content.last_decision_id,
                            updated_at=datetime.now(UTC),
                        )
                    ),
                )
                if result.rowcount != 1:
                    raise CatalogConflict()
                self.session.execute(
                    delete(ContentLocalizationRow).where(
                        ContentLocalizationRow.content_id == content.id
                    )
                )
                self.session.execute(
                    delete(ContentAvailabilityRow).where(
                        ContentAvailabilityRow.content_id == content.id
                    )
                )
                self.session.execute(
                    delete(CatalogSourceRow).where(CatalogSourceRow.content_id == content.id)
                )
            self._add_children(content)
            self.session.add(
                CatalogRevisionRow(
                    content_id=content.id,
                    revision=content.revision,
                    decision_id=content.last_decision_id,
                    catalog_version=content.version.value,
                    payload={"state": content.state.value},
                    created_at=datetime.now(UTC),
                )
            )
            self.session.flush()
        except IntegrityError as exc:
            raise CatalogConflict("catalog decision or version already exists") from exc
        except OperationalError as exc:
            raise CatalogError(
                "CAT_PERSISTENCE_UNAVAILABLE", "catalog store unavailable", retryable=True
            ) from exc

    @staticmethod
    def _new_row(content: CatalogContent) -> ApprovedContentRow:
        return ApprovedContentRow(
            content_id=content.id,
            content_type=content.content_type,
            state=content.state.value,
            current_revision=content.revision,
            catalog_version=content.version.value,
            release_at=content.release_at,
            runtime_minutes=content.runtime_minutes,
            popularity=content.popularity,
            genres=sorted(content.genres),
            current_decision_id=content.last_decision_id,
            updated_at=datetime.now(UTC),
        )

    def _add_children(self, content: CatalogContent) -> None:
        for localization in content.localizations.values():
            self.session.add(
                ContentLocalizationRow(
                    content_id=content.id,
                    locale=localization.locale,
                    title=localization.title,
                    synopsis=localization.synopsis,
                    people=list(localization.people),
                )
            )
        self.session.add(
            CatalogSourceRow(
                content_id=content.id,
                provider=content.source.provider,
                source_record_id=content.source.source_record_id,
                license_reference=content.source.license_reference,
                last_success_at=content.source.last_success_at,
            )
        )
        for availability in content.availability:
            self.session.add(
                ContentAvailabilityRow(
                    id=uuid4(),
                    content_id=content.id,
                    region=availability.region,
                    provider=availability.provider,
                    verified=True,
                    verified_at=availability.verified_at,
                    starts_at=availability.starts_at,
                    ends_at=availability.ends_at,
                    direct_url=availability.direct_url,
                    detail_url=availability.detail_url,
                )
            )
