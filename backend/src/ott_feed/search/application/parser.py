"""Deterministic Korean/English structured-query parsing."""

from __future__ import annotations

import re
import unicodedata

from ott_feed.search.domain.models import StructuredQuery

SPACE = re.compile(r"\s+")
RUNTIME_PATTERNS = (
    re.compile(r"(?P<minutes>\d{1,3})\s*분\s*(?:이내|미만)?"),
    re.compile(r"(?P<hours>\d(?:\.\d+)?)\s*시간\s*(?:이내|미만)?"),
    re.compile(r"(?:under|within|max)\s+(?P<minutes>\d{1,3})\s*(?:min|minutes?)"),
)
GENRES = {
    "코미디": "comedy",
    "웃긴": "comedy",
    "comedy": "comedy",
    "드라마": "drama",
    "drama": "drama",
    "액션": "action",
    "action": "action",
    "로맨스": "romance",
    "romance": "romance",
    "다큐": "documentary",
    "documentary": "documentary",
}


def normalize_query(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return SPACE.sub(" ", normalized)


def parse_query(value: str, locale: str) -> StructuredQuery:
    normalized = normalize_query(value)
    runtime: int | None = None
    consumed: set[str] = set()
    for pattern in RUNTIME_PATTERNS:
        match = pattern.search(normalized)
        if match:
            runtime = (
                int(match.group("minutes"))
                if match.groupdict().get("minutes")
                else round(float(match.group("hours")) * 60)
            )
            consumed.update(match.group(0).split())
            break
    genres = frozenset(canonical for term, canonical in GENRES.items() if term in normalized)
    consumed.update(term for term in GENRES if term in normalized)
    unresolved = tuple(
        token
        for token in normalized.split()
        if token not in consumed and not token.isdigit() and len(token) > 1
    )
    return StructuredQuery(
        text=normalized,
        locale=locale,
        genres=genres,
        max_runtime_minutes=runtime,
        unresolved_terms=unresolved,
    )
