"""Source-aware deterministic field merge and tombstone closure."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from ott_feed.ingestion.domain.models import (
    MergedMetadata,
    NormalizedMetadata,
    SourceFieldCandidate,
)


class MergeEngine:
    def __init__(self, authority: Mapping[str, int], version: str = "merge-v1") -> None:
        self.authority = authority
        self.version = version

    def merge(
        self,
        *,
        merged_id: str,
        canonical_content_id: str,
        inputs: Sequence[tuple[str, datetime, NormalizedMetadata]],
        computed_at: datetime,
    ) -> MergedMetadata:
        candidates: list[SourceFieldCandidate] = []
        for provider_id, observed_at, value in inputs:
            rank = self.authority.get(provider_id, 0)
            candidates.extend(
                SourceFieldCandidate(
                    f"title.{locale}", title, provider_id, value.normalized_id, observed_at, rank
                )
                for locale, title in value.localized_titles
            )
            candidates.extend(
                SourceFieldCandidate(
                    f"identifier.{namespace}",
                    external_id,
                    provider_id,
                    value.normalized_id,
                    observed_at,
                    rank,
                )
                for namespace, external_id in value.identifiers
            )
            if value.runtime_minutes is not None:
                candidates.append(
                    SourceFieldCandidate(
                        "runtime_minutes",
                        str(value.runtime_minutes),
                        provider_id,
                        value.normalized_id,
                        observed_at,
                        rank,
                    )
                )
        grouped: dict[str, list[SourceFieldCandidate]] = {}
        for candidate in candidates:
            grouped.setdefault(candidate.path, []).append(candidate)
        selected: list[SourceFieldCandidate] = []
        alternatives: list[SourceFieldCandidate] = []
        for path in sorted(grouped):
            ordered = sorted(
                grouped[path],
                key=lambda item: (
                    -item.authority,
                    -item.observed_at.timestamp(),
                    item.provider_id,
                    item.normalized_id,
                    item.value,
                ),
            )
            selected.append(ordered[0])
            alternatives.extend(ordered[1:])
        input_ids = tuple(sorted(value.normalized_id for _, _, value in inputs))
        return MergedMetadata(
            merged_id,
            canonical_content_id,
            self.version,
            input_ids,
            tuple(selected),
            tuple(alternatives),
            computed_at,
        )


def should_withdraw(removed_provider: str, active_authoritative_providers: frozenset[str]) -> bool:
    return not (active_authoritative_providers - {removed_provider})
