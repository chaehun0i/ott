"""Pure U04 provider-policy and backpressure decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.ingestion.domain.errors import PolicyViolation
from ott_feed.ingestion.domain.models import ProviderPolicy

RESERVED_LANES = frozenset({"u04_withdrawal", "u04_publication"})


def require_collection(policy: ProviderPolicy, region: str, at: datetime) -> None:
    if not policy.active_at(at):
        raise PolicyViolation("POLICY_INACTIVE", "provider policy is not active")
    if "collect" not in policy.allowed_uses:
        raise PolicyViolation("POLICY_USE_DENIED", "collection is not permitted")
    if region not in policy.regions:
        raise PolicyViolation("POLICY_REGION_DENIED", "collection region is not permitted")


@dataclass(frozen=True, slots=True)
class BackpressureState:
    memory_ratio: float = 0.0
    pool_wait_ms: int = 0
    pending_publication_seconds: int = 0
    disk_ratio: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.memory_ratio <= 1 or not 0 <= self.disk_ratio <= 1:
            raise ValueError("resource ratios must be within [0, 1]")
        if self.pool_wait_ms < 0 or self.pending_publication_seconds < 0:
            raise ValueError("wait and age values cannot be negative")

    @property
    def constrained(self) -> bool:
        return (
            self.memory_ratio >= 0.8
            or self.pool_wait_ms >= 1_000
            or self.pending_publication_seconds >= 300
            or self.disk_ratio >= 0.8
        )

    def permits(self, lane: str) -> bool:
        return not self.constrained or lane in RESERVED_LANES
