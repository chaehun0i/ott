"""Provider-scoped circuit state independent from HTTP and persistence."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from time import monotonic

from ott_feed.ingestion.domain.errors import ProviderTransientError


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class ProviderCircuit:
    window: int = 20
    failure_ratio: float = 0.5
    open_seconds: float = 30.0
    half_open_probes: int = 2
    clock: Callable[[], float] = monotonic
    state: CircuitState = CircuitState.CLOSED
    outcomes: deque[bool] = field(default_factory=deque)
    opened_at: float | None = None
    probes_remaining: int = 0
    _lock: Lock = field(default_factory=Lock)

    def before_call(self) -> None:
        with self._lock:
            if self.state is CircuitState.OPEN:
                if self.opened_at is None or self.clock() - self.opened_at < self.open_seconds:
                    raise ProviderTransientError(
                        "PROVIDER_CIRCUIT_OPEN", "provider circuit is open"
                    )
                self.state = CircuitState.HALF_OPEN
                self.probes_remaining = self.half_open_probes
            if self.state is CircuitState.HALF_OPEN:
                if self.probes_remaining <= 0:
                    raise ProviderTransientError(
                        "PROVIDER_CIRCUIT_OPEN", "provider probes are exhausted"
                    )
                self.probes_remaining -= 1

    def record(self, success: bool) -> None:
        with self._lock:
            if self.state is CircuitState.HALF_OPEN:
                if success and self.probes_remaining == 0:
                    self._close()
                elif not success:
                    self._open()
                return
            self.outcomes.append(success)
            while len(self.outcomes) > self.window:
                self.outcomes.popleft()
            if len(self.outcomes) == self.window:
                failures = sum(not item for item in self.outcomes)
                if failures / self.window >= self.failure_ratio:
                    self._open()

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = self.clock()
        self.probes_remaining = 0

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.probes_remaining = 0
        self.outcomes.clear()
