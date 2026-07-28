"""Deterministic provider-fair scheduling with reserved safety lanes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ott_feed.ingestion.domain.policies import BackpressureState

LANE_PRIORITY = {
    "u04_withdrawal": 0,
    "u04_publication": 1,
    "u04_incremental": 2,
    "u04_revalidation": 3,
    "u04_full_sync": 4,
    "u04_retention": 5,
}


@dataclass(frozen=True, slots=True)
class ScheduledWork:
    work_id: str
    provider_id: str
    lane: str
    ready_at: datetime
    priority: int = 100

    def __post_init__(self) -> None:
        if self.lane not in LANE_PRIORITY:
            raise ValueError(f"unknown U04 lane: {self.lane}")


class ProviderFairScheduler:
    def select(
        self,
        candidates: tuple[ScheduledWork, ...],
        now: datetime,
        limit: int,
        backpressure: BackpressureState,
        provider_offset: int = 0,
    ) -> tuple[ScheduledWork, ...]:
        if limit <= 0:
            raise ValueError("selection limit must be positive")
        eligible = [
            item for item in candidates if item.ready_at <= now and backpressure.permits(item.lane)
        ]
        eligible.sort(key=lambda item: (LANE_PRIORITY[item.lane], item.priority, item.work_id))
        selected: list[ScheduledWork] = []
        while eligible and len(selected) < limit:
            best_lane = LANE_PRIORITY[eligible[0].lane]
            lane_items = [item for item in eligible if LANE_PRIORITY[item.lane] == best_lane]
            providers = sorted({item.provider_id for item in lane_items})
            if providers:
                shift = provider_offset % len(providers)
                providers = providers[shift:] + providers[:shift]
            for provider_id in providers:
                item = next(item for item in lane_items if item.provider_id == provider_id)
                selected.append(item)
                eligible.remove(item)
                if len(selected) == limit:
                    break
        return tuple(selected)
