"""Deadline-aware retry, circuit breaker and bulkhead primitives."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import TypeVar

from ott_feed.platform.domain.errors import PlatformError

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class DependencyPolicy:
    dependency_id: str
    timeout_seconds: float
    max_attempts: int = 1
    retry_safe: bool = False
    base_backoff_seconds: float = 0.1
    failure_threshold: int = 5
    reset_after_seconds: float = 30.0


@dataclass(slots=True)
class CircuitBreaker:
    policy: DependencyPolicy
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    opened_at: datetime | None = None

    def allow(self, now: datetime) -> bool:
        if self.state != CircuitState.OPEN:
            return True
        if self.opened_at and now - self.opened_at >= timedelta(
            seconds=self.policy.reset_after_seconds
        ):
            self.state = CircuitState.HALF_OPEN
            return True
        return False

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self.state = CircuitState.CLOSED

    def failure(self, now: datetime) -> None:
        self.failures += 1
        if self.failures >= self.policy.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = now


@dataclass(slots=True)
class BulkheadRegistry:
    limits: dict[str, int]
    _semaphores: dict[str, asyncio.Semaphore] = field(init=False)

    def __post_init__(self) -> None:
        self._semaphores = {name: asyncio.Semaphore(limit) for name, limit in self.limits.items()}

    def semaphore(self, pool: str) -> asyncio.Semaphore:
        return self._semaphores[pool]


class ResilientExecutor:
    def __init__(self, bulkheads: BulkheadRegistry) -> None:
        self.bulkheads = bulkheads
        self.circuits: dict[str, CircuitBreaker] = {}

    async def execute(
        self,
        policy: DependencyPolicy,
        pool: str,
        operation: Callable[[], Awaitable[T]],
        absolute_deadline: datetime,
        fallback: Callable[[], Awaitable[T]] | None = None,
    ) -> T:
        circuit = self.circuits.setdefault(policy.dependency_id, CircuitBreaker(policy))
        now = datetime.now(UTC)
        if not circuit.allow(now):
            if fallback:
                return await fallback()
            raise PlatformError(
                "dependency_circuit_open", "Dependency is temporarily unavailable", 503, True
            )

        attempts = policy.max_attempts if policy.retry_safe else 1
        async with self.bulkheads.semaphore(pool):
            for attempt in range(1, attempts + 1):
                remaining = (absolute_deadline - datetime.now(UTC)).total_seconds()
                timeout = min(policy.timeout_seconds, remaining)
                if timeout <= 0:
                    break
                try:
                    result = await asyncio.wait_for(operation(), timeout=timeout)
                    circuit.success()
                    return result
                except (TimeoutError, OSError):
                    circuit.failure(datetime.now(UTC))
                    if attempt < attempts:
                        delay = policy.base_backoff_seconds * (2 ** (attempt - 1))
                        delay *= random.uniform(0.5, 1.5)
                        if datetime.now(UTC) + timedelta(seconds=delay) < absolute_deadline:
                            await asyncio.sleep(delay)
                            continue
                    break
        if fallback:
            return await fallback()
        raise PlatformError("dependency_unavailable", "Dependency is unavailable", 503, True)


DEFAULT_POOL_LIMITS = {
    "api_database": 10,
    "worker_database": 5,
    "ai_http": 4,
    "provider_http": 4,
    "oauth_http": 2,
    "notification_http": 2,
}
