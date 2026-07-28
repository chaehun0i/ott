"""Cost-aware, single-host token bucket rate limiting for the prototype."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic

from ott_feed.platform.domain.errors import PlatformError


@dataclass(frozen=True, slots=True)
class RatePolicy:
    capacity: float
    refill_per_second: float


@dataclass(slots=True)
class _Bucket:
    tokens: float
    updated_at: float


DEFAULT_POLICIES = {
    "public": RatePolicy(60, 1),
    "authentication": RatePolicy(10, 0.1),
    "recommendation": RatePolicy(12, 0.2),
    "administration": RatePolicy(20, 0.2),
}


class InMemoryRateLimiter:
    def __init__(self, policies: dict[str, RatePolicy] | None = None) -> None:
        self.policies = policies or DEFAULT_POLICIES
        self._buckets: dict[tuple[str, str], _Bucket] = {}
        self._lock = Lock()

    def consume(self, bucket_class: str, subject: str, cost: float = 1.0) -> None:
        policy = self.policies[bucket_class]
        key = (bucket_class, subject)
        now = monotonic()
        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket(policy.capacity, now))
            elapsed = max(0.0, now - bucket.updated_at)
            bucket.tokens = min(policy.capacity, bucket.tokens + elapsed * policy.refill_per_second)
            bucket.updated_at = now
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return
            retry_after = max(1, int((cost - bucket.tokens) / policy.refill_per_second) + 1)
        raise PlatformError(
            "rate_limit_exceeded",
            "Request rate limit exceeded",
            status_code=429,
            retryable=True,
            safe_details={"retryAfterSeconds": retry_after},
        )
