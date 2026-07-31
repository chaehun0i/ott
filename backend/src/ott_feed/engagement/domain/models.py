"""Notification delivery domain models."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from ott_feed.engagement.domain.errors import InvalidTransition, StaleFencingToken


class Channel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"


class JobStatus(StrEnum):
    READY = "ready"
    CLAIMED = "claimed"
    RETRY = "retry"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    TERMINAL = "terminal"


TERMINAL_STATUSES = frozenset({JobStatus.DELIVERED, JobStatus.CANCELLED, JobStatus.TERMINAL})


@dataclass(frozen=True, slots=True)
class NotificationEvent:
    event_id: str
    content_id: str
    content_version: int
    event_type: str
    effective_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.event_id or not self.content_id or not self.event_type:
            raise ValueError("event identifiers and type are required")
        if self.content_version <= 0:
            raise ValueError("content_version must be positive")
        if self.expires_at <= self.effective_at:
            raise ValueError("event expiry must follow effective time")


@dataclass(frozen=True, slots=True)
class DeliveryAttempt:
    attempt_number: int
    fencing_token: int
    outcome: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.attempt_number <= 0 or self.fencing_token <= 0:
            raise ValueError("attempt and fencing token must be positive")
        if not self.outcome:
            raise ValueError("attempt outcome is required")


@dataclass(frozen=True, slots=True)
class DeliveryJob:
    job_id: str
    deduplication_key: str
    event_id: str
    member_ref: str
    channel: Channel
    available_at: datetime
    expires_at: datetime
    status: JobStatus = JobStatus.READY
    attempt_count: int = 0
    fencing_token: int = 0
    lease_owner: str | None = None
    lease_until: datetime | None = None

    def __post_init__(self) -> None:
        if not all((self.job_id, self.deduplication_key, self.event_id, self.member_ref)):
            raise ValueError("job identifiers are required")
        if self.expires_at <= self.available_at:
            raise ValueError("job expiry must follow availability")
        if self.attempt_count < 0 or self.fencing_token < 0:
            raise ValueError("counters cannot be negative")
        if self.status is JobStatus.CLAIMED and (not self.lease_owner or not self.lease_until):
            raise ValueError("claimed job requires a lease")

    def claim(self, owner: str, now: datetime, lease_until: datetime) -> DeliveryJob:
        if not owner or lease_until <= now:
            raise ValueError("owner and future lease are required")
        if self.status in TERMINAL_STATUSES or self.expires_at <= now:
            raise InvalidTransition("terminal or expired job cannot be claimed")
        if self.status is JobStatus.CLAIMED and self.lease_until and self.lease_until > now:
            raise InvalidTransition("active lease cannot be stolen")
        return replace(
            self,
            status=JobStatus.CLAIMED,
            fencing_token=self.fencing_token + 1,
            lease_owner=owner,
            lease_until=lease_until,
        )

    def heartbeat(self, owner: str, token: int, lease_until: datetime) -> DeliveryJob:
        self._require_current(owner, token)
        if self.lease_until is None or lease_until <= self.lease_until:
            raise InvalidTransition("heartbeat must extend the lease")
        return replace(self, lease_until=lease_until)

    def complete(self, owner: str, token: int, delivered: bool) -> DeliveryJob:
        self._require_current(owner, token)
        status = JobStatus.DELIVERED if delivered else JobStatus.TERMINAL
        return replace(
            self,
            status=status,
            attempt_count=self.attempt_count + 1,
            lease_owner=None,
            lease_until=None,
        )

    def retry(self, owner: str, token: int, available_at: datetime) -> DeliveryJob:
        self._require_current(owner, token)
        if available_at >= self.expires_at:
            raise InvalidTransition("retry cannot start at or after expiry")
        return replace(
            self,
            status=JobStatus.RETRY,
            attempt_count=self.attempt_count + 1,
            available_at=available_at,
            lease_owner=None,
            lease_until=None,
        )

    def cancel(self) -> DeliveryJob:
        if self.status in TERMINAL_STATUSES:
            return self
        return replace(self, status=JobStatus.CANCELLED, lease_owner=None, lease_until=None)

    def _require_current(self, owner: str, token: int) -> None:
        if (
            self.status is not JobStatus.CLAIMED
            or self.lease_owner != owner
            or self.fencing_token != token
        ):
            raise StaleFencingToken("worker lease or fencing token is stale")
