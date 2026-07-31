"""Pure U06 health truth model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class HealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HealthContribution:
    component: str
    state: HealthState
    required: bool
    observed_at: datetime
    freshness: timedelta
    reason: str

    def is_fresh(self, now: datetime) -> bool:
        return now - self.observed_at <= self.freshness


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    live: bool
    ready: bool
    status: HealthState
    reasons: tuple[str, ...]


def aggregate_health(
    contributions: tuple[HealthContribution, ...], now: datetime, process_alive: bool = True
) -> HealthSnapshot:
    ordered = sorted(
        contributions,
        key=lambda item: (
            item.component,
            item.required,
            item.state.value,
            item.observed_at,
            item.freshness,
            item.reason,
        ),
    )
    invalid_required = [
        item
        for item in ordered
        if item.required and (not item.is_fresh(now) or item.state is not HealthState.HEALTHY)
    ]
    degraded = [
        item
        for item in ordered
        if not item.required and (not item.is_fresh(now) or item.state is not HealthState.HEALTHY)
    ]
    ready = process_alive and not invalid_required
    status = (
        HealthState.UNHEALTHY
        if not process_alive or invalid_required
        else HealthState.DEGRADED
        if degraded
        else HealthState.HEALTHY
    )
    reasons = tuple(item.reason for item in (*invalid_required, *degraded))
    return HealthSnapshot(process_alive, ready, status, reasons)
