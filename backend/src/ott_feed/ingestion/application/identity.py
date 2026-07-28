"""Deterministic tiered canonical identity resolution."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from ott_feed.ingestion.domain.models import (
    CanonicalIdentityCandidate,
    IdentityDecision,
    NormalizedMetadata,
)


class IdentityResolver:
    def __init__(
        self,
        tiers: tuple[str, ...],
        crosswalk: Mapping[tuple[str, str], frozenset[str]],
        new_content_id: Callable[[], str],
        policy_version: str = "identity-v1",
    ) -> None:
        if not tiers or len(tiers) != len(set(tiers)):
            raise ValueError("identity tiers must be non-empty and unique")
        self.tiers = tiers
        self.crosswalk = crosswalk
        self.new_content_id = new_content_id
        self.policy_version = policy_version

    def resolve(self, value: NormalizedMetadata, resolution_id: str) -> CanonicalIdentityCandidate:
        identifiers = dict(value.identifiers)
        for tier in self.tiers:
            external_id = identifiers.get(tier)
            if external_id is None:
                continue
            candidates = tuple(sorted(self.crosswalk.get((tier, external_id), frozenset())))
            if len(candidates) == 1:
                return CanonicalIdentityCandidate(
                    resolution_id,
                    value.normalized_id,
                    self.policy_version,
                    IdentityDecision.MATCHED,
                    candidates,
                    candidates[0],
                    tier,
                )
            if len(candidates) > 1:
                return CanonicalIdentityCandidate(
                    resolution_id,
                    value.normalized_id,
                    self.policy_version,
                    IdentityDecision.AMBIGUOUS,
                    candidates,
                    None,
                    tier,
                )
        content_id = self.new_content_id()
        return CanonicalIdentityCandidate(
            resolution_id,
            value.normalized_id,
            self.policy_version,
            IdentityDecision.NEW,
            (),
            content_id,
            None,
        )
