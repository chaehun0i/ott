"""Deterministic email retry and circuit isolation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


RETRY_DELAYS = (timedelta(seconds=5), timedelta(seconds=30), timedelta(minutes=5))


def retry_at(attempt: int, now: datetime, jitter_seconds: float = 0) -> datetime:
    if attempt < 1 or attempt > len(RETRY_DELAYS):
        raise ValueError("attempt is outside the retry policy")
    if not 0 <= jitter_seconds <= 1:
        raise ValueError("jitter must be between zero and one second")
    return now + RETRY_DELAYS[attempt - 1] + timedelta(seconds=jitter_seconds)


@dataclass(slots=True)
class EmailCircuit:
    state: CircuitState = CircuitState.CLOSED
    opened_at: datetime | None = None
    results: deque[bool] = field(default_factory=lambda: deque(maxlen=20))

    def allow(self, now: datetime) -> bool:
        if self.state is CircuitState.OPEN and self.opened_at:
            if now - self.opened_at >= timedelta(seconds=30):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record(self, success: bool, now: datetime) -> None:
        if self.state is CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED if success else CircuitState.OPEN
            self.opened_at = None if success else now
            self.results.clear()
            return
        self.results.append(success)
        if (
            len(self.results) >= 10
            and sum(not item for item in self.results) / len(self.results) >= 0.5
        ):
            self.state = CircuitState.OPEN
            self.opened_at = now
