"""Privacy-safe search telemetry; query and vector values are never accepted."""

from __future__ import annotations

from ott_feed.platform.telemetry import Metrics


class SearchTelemetry:
    def __init__(self, metrics: Metrics | None = None) -> None:
        self.metrics = metrics or Metrics()

    def result(self, *, degraded_reason: str | None, result_count: int) -> None:
        bucket = "zero" if result_count == 0 else "one_to_nine" if result_count < 10 else "ten_plus"
        self.metrics.increment(
            "search_result_total",
            degraded=degraded_reason or "none",
            count_bucket=bucket,
        )

    def fallback(self, reason: str) -> None:
        self.metrics.increment("search_fallback_total", reason=reason)
