"""Allowlisted catalog metrics without content payloads."""

from __future__ import annotations

from ott_feed.platform.telemetry import Metrics

CATALOG_METRICS = frozenset(
    {
        "catalog_closure_drop_total",
        "catalog_projection_gap_total",
        "catalog_projection_lag_total",
        "catalog_stale_total",
        "catalog_rebuild_total",
    }
)
ALLOWED_ATTRIBUTES = frozenset({"region", "provider", "projection", "reason", "locale"})


class CatalogTelemetry:
    def __init__(self, metrics: Metrics | None = None) -> None:
        self.metrics = metrics or Metrics()

    def increment(self, metric: str, attributes: dict[str, str] | None = None) -> None:
        if metric not in CATALOG_METRICS:
            raise ValueError("catalog metric is not allowlisted")
        safe = {
            key: value for key, value in (attributes or {}).items() if key in ALLOWED_ATTRIBUTES
        }
        self.metrics.increment(metric, **safe)
