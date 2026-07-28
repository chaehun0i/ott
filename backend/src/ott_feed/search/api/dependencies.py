"""Search rate-limit adapter over the shared token-bucket implementation."""

from ott_feed.platform.application.rate_limit import InMemoryRateLimiter
from ott_feed.platform.domain.errors import PlatformError


class SearchRateLimitAdapter:
    def __init__(self, limiter: InMemoryRateLimiter) -> None:
        self.limiter = limiter

    def allow(self, bucket: str, subject: str, cost: int = 1) -> bool:
        try:
            self.limiter.consume(bucket, subject, float(cost))
        except (PlatformError, KeyError):
            return False
        return True
