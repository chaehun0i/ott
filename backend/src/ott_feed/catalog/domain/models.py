"""Immutable approved-catalog values and explicit state transitions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from ott_feed.catalog.domain.errors import CatalogError

ContentId = str


class CatalogState(StrEnum):
    APPROVED = "approved"
    WITHDRAWN = "withdrawn"


class GenerationState(StrEnum):
    BUILDING = "building"
    VALIDATED = "validated"
    ACTIVE = "active"
    RETIRED = "retired"
    FAILED = "failed"


@dataclass(frozen=True, order=True, slots=True)
class CatalogVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise CatalogError("CAT_VERSION_INVALID", "catalog version must be positive")

    def next(self) -> CatalogVersion:
        return CatalogVersion(self.value + 1)


@dataclass(frozen=True, slots=True)
class Localization:
    locale: str
    title: str
    synopsis: str
    people: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.locale or not self.title:
            raise CatalogError("LOC_REQUIRED", "locale and title are required")


@dataclass(frozen=True, slots=True)
class Availability:
    region: str
    provider: str
    verified_at: datetime
    starts_at: datetime
    ends_at: datetime | None = None
    direct_url: str | None = None
    detail_url: str | None = None

    def __post_init__(self) -> None:
        if not self.region or not self.provider:
            raise CatalogError("AVAIL_REQUIRED", "region and provider are required")
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise CatalogError("AVAIL_WINDOW_INVALID", "availability window is invalid")
        if not self.direct_url and not self.detail_url:
            raise CatalogError("AVAIL_LINK_REQUIRED", "a lawful provider link is required")

    def active_at(self, instant: datetime) -> bool:
        return self.starts_at <= instant and (self.ends_at is None or instant < self.ends_at)

    @property
    def preferred_url(self) -> str:
        return self.direct_url or self.detail_url or ""


@dataclass(frozen=True, slots=True)
class CatalogSource:
    provider: str
    source_record_id: str
    license_reference: str
    last_success_at: datetime

    def __post_init__(self) -> None:
        if not all((self.provider, self.source_record_id, self.license_reference)):
            raise CatalogError("CAT_PROVENANCE_REQUIRED", "source and license are required")


@dataclass(frozen=True, slots=True)
class CatalogRevision:
    revision: int
    decision_id: str
    version: CatalogVersion
    created_at: datetime


@dataclass(slots=True)
class CatalogContent:
    id: ContentId
    content_type: str
    genres: frozenset[str]
    release_at: datetime
    runtime_minutes: int | None
    popularity: float
    localizations: dict[str, Localization]
    availability: tuple[Availability, ...]
    source: CatalogSource
    state: CatalogState = CatalogState.APPROVED
    version: CatalogVersion = field(default_factory=lambda: CatalogVersion(1))
    revision: int = 1
    last_decision_id: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.content_type or not self.localizations:
            raise CatalogError(
                "CAT_REQUIRED", "content identity, type and localization are required"
            )
        if self.runtime_minutes is not None and self.runtime_minutes <= 0:
            raise CatalogError("CAT_RUNTIME_INVALID", "runtime must be positive")
        if not 0 <= self.popularity <= 1:
            raise CatalogError("CAT_POPULARITY_INVALID", "popularity must be within [0, 1]")

    def replaced(self, newer: CatalogContent, decision_id: str) -> CatalogContent:
        if newer.id != self.id:
            raise CatalogError("CAT_ID_IMMUTABLE", "content ID cannot change")
        return replace(
            newer,
            version=self.version.next(),
            revision=self.revision + 1,
            state=CatalogState.APPROVED,
            last_decision_id=decision_id,
        )

    def withdraw(self, decision_id: str) -> None:
        if self.last_decision_id == decision_id:
            return
        self.state = CatalogState.WITHDRAWN
        self.version = self.version.next()
        self.revision += 1
        self.last_decision_id = decision_id

    def reactivate(self, decision_id: str) -> None:
        if self.last_decision_id == decision_id:
            return
        self.state = CatalogState.APPROVED
        self.version = self.version.next()
        self.revision += 1
        self.last_decision_id = decision_id


@dataclass(slots=True)
class ProjectionGeneration:
    id: str
    projection: str
    catalog_version: CatalogVersion
    state: GenerationState = GenerationState.BUILDING

    def validate(self) -> None:
        if self.state is not GenerationState.BUILDING:
            raise CatalogError("PROJ_STATE_INVALID", "only building generations can validate")
        self.state = GenerationState.VALIDATED

    def activate(self) -> None:
        if self.state is not GenerationState.VALIDATED:
            raise CatalogError("PROJ_STATE_INVALID", "only validated generations can activate")
        self.state = GenerationState.ACTIVE

    def fail(self) -> None:
        if self.state is GenerationState.ACTIVE:
            raise CatalogError(
                "PROJ_ACTIVE_FAIL_FORBIDDEN", "active generation cannot fail in place"
            )
        self.state = GenerationState.FAILED


@dataclass(frozen=True, slots=True)
class FeedCursor:
    fingerprint: str
    generation: str
    score: float
    content_id: ContentId
