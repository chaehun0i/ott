"""Framework-free, versioned U06 dependency ports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...


class RandomSource(Protocol):
    def uniform(self, lower: float, upper: float) -> float: ...


class IdGenerator(Protocol):
    def new(self) -> str: ...


class AuthorizationDecisionPort(Protocol):
    def decide(self, actor_ref: str, permission: str) -> Mapping[str, object]: ...


class NotificationPreferencePort(Protocol):
    def eligible(self, event_type: str, cursor: str | None, limit: int) -> Sequence[object]: ...


class ApprovedNotificationEventPort(Protocol):
    def get_approved(self, event_id: str, version: int) -> Mapping[str, object] | None: ...


class AdminCatalogCommandPort(Protocol):
    def apply(
        self, command: Mapping[str, object], timeout_seconds: float
    ) -> Mapping[str, object]: ...


class RecommendationTracePort(Protocol):
    def read_allowlisted(self, trace_id: str, limit: int) -> Mapping[str, object] | None: ...


class HealthContributionPort(Protocol):
    def check(self, deadline: float) -> Mapping[str, object]: ...


class ChannelDeliveryPort(Protocol):
    def deliver(
        self,
        channel: str,
        payload: Mapping[str, object],
        idempotency_key: str,
        timeout_seconds: float,
    ) -> Mapping[str, object]: ...


class TelemetryPort(Protocol):
    def increment(self, metric: str, attributes: Mapping[str, str] | None = None) -> None: ...

    def observe(
        self, metric: str, value: float, attributes: Mapping[str, str] | None = None
    ) -> None: ...
