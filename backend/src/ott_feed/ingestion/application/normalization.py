"""Pure versioned provider-to-canonical normalization."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

from ott_feed.ingestion.domain.models import NormalizedMetadata


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _string_pairs(value: object, path: str) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return (), ()
    pairs: list[tuple[str, str]] = []
    paths: list[str] = []
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str):
            normalized = normalize_text(item)
            if normalized:
                pairs.append((key, normalized))
                paths.append(f"{path}.{key}")
    pairs.sort()
    paths.sort()
    return tuple(pairs), tuple(paths)


def _genres(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    normalized = {
        normalize_text(item).casefold() for item in value if isinstance(item, str) and item.strip()
    }
    return tuple(sorted(normalized))


class MetadataNormalizer:
    def __init__(self, version: str = "normalization-v1") -> None:
        if not version:
            raise ValueError("normalization version is required")
        self.version = version

    def normalize(
        self,
        payload: Mapping[str, object],
        *,
        raw_record_id: str,
        normalized_id: str,
    ) -> NormalizedMetadata:
        identifiers, identifier_paths = _string_pairs(payload.get("external_ids"), "external_ids")
        titles, title_paths = _string_pairs(payload.get("titles"), "titles")
        runtime_value = payload.get("runtime_minutes")
        runtime = runtime_value if isinstance(runtime_value, int) and runtime_value > 0 else None
        content_type_value = payload.get("content_type")
        content_type = (
            normalize_text(content_type_value).casefold()
            if isinstance(content_type_value, str) and content_type_value.strip()
            else "unknown"
        )
        genres = _genres(payload.get("genres"))
        source_paths = list(identifier_paths + title_paths)
        if runtime is not None:
            source_paths.append("runtime_minutes")
        if content_type != "unknown":
            source_paths.append("content_type")
        if genres:
            source_paths.append("genres")
        return NormalizedMetadata(
            normalized_id=normalized_id,
            raw_record_id=raw_record_id,
            normalization_version=self.version,
            content_type=content_type,
            identifiers=identifiers,
            localized_titles=titles,
            runtime_minutes=runtime,
            genres=genres,
            source_paths=tuple(sorted(source_paths)),
        )

    def normalize_existing(self, value: NormalizedMetadata) -> NormalizedMetadata:
        if value.normalization_version != self.version:
            raise ValueError("normalized value uses another version")
        return value
