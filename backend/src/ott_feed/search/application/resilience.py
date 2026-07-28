"""Pure bounded circuit state used by the embedding adapter."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from time import monotonic

from ott_feed.search.domain.errors import EmbeddingUnavailable


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class EmbeddingCircuit:
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
                    raise EmbeddingUnavailable("SEARCH_EMBEDDING_CIRCUIT_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.probes_remaining = self.half_open_probes
            if self.state is CircuitState.HALF_OPEN:
                if self.probes_remaining <= 0:
                    raise EmbeddingUnavailable("SEARCH_EMBEDDING_CIRCUIT_OPEN")
                self.probes_remaining -= 1

    def record(self, success: bool) -> None:
        with self._lock:
            if self.state is CircuitState.HALF_OPEN:
                if success:
                    if self.probes_remaining == 0:
                        self._close()
                else:
                    self._open()
                return
            self.outcomes.append(success)
            while len(self.outcomes) > self.window:
                self.outcomes.popleft()
            if len(self.outcomes) == self.window:
                failures = sum(not outcome for outcome in self.outcomes)
                if failures / self.window >= self.failure_ratio:
                    self._open()

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = self.clock()
        self.probes_remaining = 0

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.outcomes.clear()
        self.probes_remaining = 0
