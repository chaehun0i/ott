"""Small deterministic circuit and usage guards for the AI dependency."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from ott_feed.recommendation.domain.errors import unavailable


@dataclass(slots=True)
class AICircuit:
    window: int = 20
    failure_ratio: float = 0.5
    outcomes: deque[bool] = field(default_factory=deque)
    opened: bool = False

    def allow(self) -> None:
        if self.opened:
            raise unavailable("ai_circuit_open", "AI provider circuit is open")

    def record(self, success: bool) -> None:
        self.outcomes.append(success)
        while len(self.outcomes) > self.window:
            self.outcomes.popleft()
        if len(self.outcomes) == self.window:
            failures = sum(not outcome for outcome in self.outcomes)
            self.opened = failures / self.window >= self.failure_ratio

    def probe(self, success: bool) -> None:
        if success:
            self.outcomes.clear()
            self.opened = False


@dataclass(slots=True)
class UsageGuard:
    daily_limit: int
    used: int = 0

    def reserve(self, units: int) -> None:
        if units <= 0 or self.used + units > self.daily_limit:
            raise unavailable("ai_budget_exhausted", "AI usage budget exhausted")
        self.used += units
