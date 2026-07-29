"""Immutable recommendation values and response-safe types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from ott_feed.recommendation.domain.errors import invalid


class Locale(StrEnum):
    KO = "ko-KR"
    EN = "en-US"


class ConditionKind(StrEnum):
    GENRE = "genre"
    MAX_RUNTIME = "max_runtime"
    OTT = "ott"
    REGION = "region"
    MOOD = "mood"
    COMPANION = "companion"
    AGE_RATING = "age_rating"


class ValidationState(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    MISSING = "missing"
    ERROR = "error"


class DegradedReason(StrEnum):
    AI_UNAVAILABLE = "ai_unavailable"
    AI_BUDGET_EXHAUSTED = "ai_budget_exhausted"
    NON_PERSONALIZED = "non_personalized"


@dataclass(frozen=True, slots=True, order=True)
class Condition:
    kind: ConditionKind
    value: str
    hard: bool = True

    def __post_init__(self) -> None:
        canonical = self.value.strip().casefold()
        if not canonical or len(canonical) > 128:
            raise invalid("invalid_condition", "condition value is invalid")
        object.__setattr__(self, "value", canonical)


@dataclass(frozen=True, slots=True)
class IntentConflict:
    kind: ConditionKind
    previous: str
    requested: str


@dataclass(frozen=True, slots=True)
class RecommendationIntent:
    locale: Locale
    conditions: tuple[Condition, ...]
    version: str = "intent-v1"
    conflicts: tuple[IntentConflict, ...] = ()

    def __post_init__(self) -> None:
        if len(self.conditions) > 32:
            raise invalid("too_many_conditions", "at most 32 conditions are allowed")
        kinds = [condition.kind for condition in self.conditions]
        if len(kinds) != len(set(kinds)):
            raise invalid("duplicate_condition", "condition kinds must be unique")

    def condition(self, kind: ConditionKind) -> Condition | None:
        return next((item for item in self.conditions if item.kind is kind), None)


@dataclass(frozen=True, slots=True)
class ApprovedCandidate:
    content_id: str
    metadata_version: str
    title: str
    synopsis: str
    genres: tuple[str, ...]
    runtime_minutes: int
    region: str
    ott: tuple[str, ...]
    age_rating: int
    freshness: float = 0.0
    popularity: float = 0.0
    franchise: str | None = None

    def __post_init__(self) -> None:
        if not self.content_id or not self.metadata_version or not self.title:
            raise invalid("invalid_candidate", "candidate identity and title are required")
        if self.runtime_minutes <= 0 or self.age_rating < 0:
            raise invalid("invalid_candidate", "candidate bounds are invalid")


@dataclass(frozen=True, slots=True)
class FeatureContext:
    values: Mapping[str, float] = field(default_factory=dict)
    consented: bool = False
    version: str | None = None

    def __post_init__(self) -> None:
        clean = {str(key): float(value) for key, value in self.values.items()}
        object.__setattr__(self, "values", MappingProxyType(clean))


@dataclass(frozen=True, slots=True)
class ScoreProof:
    request_fit: float
    affinity: float
    freshness: float
    popularity: float
    novelty: float

    @property
    def total(self) -> float:
        return sum((self.request_fit, self.affinity, self.freshness, self.popularity, self.novelty))


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate: ApprovedCandidate
    proof: ScoreProof
    original_position: int


@dataclass(frozen=True, slots=True)
class Evidence:
    content_id: str
    metadata_version: str
    fields: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", MappingProxyType(dict(self.fields)))


@dataclass(frozen=True, slots=True)
class AtomicClaim:
    content_id: str
    metadata_version: str
    field_path: str
    text: str


@dataclass(frozen=True, slots=True)
class SafeRecommendationItem:
    content_id: str
    title: str
    summary: str
    reason: str
    score: float
    metadata_version: str


@dataclass(frozen=True, slots=True)
class RecommendationResponse:
    request_id: str
    intent: RecommendationIntent
    items: tuple[SafeRecommendationItem, ...]
    generated_at: datetime
    degraded_reasons: tuple[DegradedReason, ...] = ()
    confirmation_required: bool = False
