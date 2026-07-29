"""Deterministic intent fallback and explicit patch merge."""

from __future__ import annotations

import re
from collections.abc import Mapping

from ott_feed.recommendation.domain.errors import invalid
from ott_feed.recommendation.domain.models import (
    Condition,
    ConditionKind,
    IntentConflict,
    Locale,
    RecommendationIntent,
)

_GENRES = {
    "코미디": "comedy",
    "웃긴": "comedy",
    "comedy": "comedy",
    "드라마": "drama",
    "drama": "drama",
    "액션": "action",
    "action": "action",
}


def deterministic_intent(text: str, locale: Locale) -> RecommendationIntent:
    if len(text.encode("utf-8")) > 4096:
        raise invalid("input_too_large", "request text exceeds 4 KiB")
    lowered = text.casefold()
    values: dict[ConditionKind, str] = {}
    for token, canonical in _GENRES.items():
        if token in lowered:
            values[ConditionKind.GENRE] = canonical
            break
    runtime = re.search(r"(\d{1,3})\s*(?:분|minutes?|mins?)", lowered)
    hour = re.search(r"(\d)\s*(?:시간|hours?)", lowered)
    if runtime:
        values[ConditionKind.MAX_RUNTIME] = runtime.group(1)
    elif hour:
        values[ConditionKind.MAX_RUNTIME] = str(int(hour.group(1)) * 60)
    conditions = tuple(Condition(kind, value) for kind, value in values.items())
    return RecommendationIntent(locale, conditions)


def merge_intent(
    current: RecommendationIntent, patch: Mapping[ConditionKind, str | None]
) -> RecommendationIntent:
    values = {condition.kind: condition.value for condition in current.conditions}
    conflicts: list[IntentConflict] = []
    for kind, requested in patch.items():
        if requested is None:
            values.pop(kind, None)
            continue
        canonical = requested.strip().casefold()
        if kind in values and values[kind] != canonical:
            conflicts.append(IntentConflict(kind, values[kind], canonical))
        values[kind] = canonical
    return RecommendationIntent(
        current.locale,
        tuple(Condition(kind, value) for kind, value in values.items()),
        current.version,
        tuple(conflicts),
    )
