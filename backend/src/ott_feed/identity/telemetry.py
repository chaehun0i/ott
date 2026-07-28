"""Bounded U02 telemetry that rejects direct identifiers and secret-bearing labels."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ott_feed.platform.telemetry import Metrics, NonBlockingTelemetryBuffer

ALLOWED_LABELS = {
    "component",
    "operation",
    "provider",
    "lane",
    "result",
    "reason",
    "key_version",
}
FORBIDDEN_LABEL_FRAGMENTS = {
    "email",
    "userid",
    "user_id",
    "oauthsubject",
    "oauth_subject",
    "sessionid",
    "session_id",
    "sessiontoken",
    "session_token",
    "payload",
    "objectreference",
    "object_reference",
    "contenttext",
}
ALLOWED_LANES = {"high", "normal", "low"}
ALLOWED_PROVIDERS = {"google"}


def validate_labels(labels: Mapping[str, str]) -> dict[str, str]:
    validated: dict[str, str] = {}
    for name, value in labels.items():
        normalized = name.lower().replace("-", "_")
        compact = normalized.replace("_", "")
        if normalized not in ALLOWED_LABELS:
            raise ValueError(f"telemetry label is not allow-listed: {name}")
        if any(fragment in {normalized, compact} for fragment in FORBIDDEN_LABEL_FRAGMENTS):
            raise ValueError(f"sensitive telemetry label rejected: {name}")
        if not value or len(value) > 80 or "@" in value:
            raise ValueError(f"telemetry label value is unsafe: {name}")
        if normalized == "lane" and value not in ALLOWED_LANES:
            raise ValueError("telemetry lane is not bounded")
        if normalized == "provider" and value not in ALLOWED_PROVIDERS:
            raise ValueError("telemetry provider is not allow-listed")
        validated[normalized] = value
    return validated


@dataclass(slots=True)
class IdentityTelemetry:
    metrics: Metrics
    events: NonBlockingTelemetryBuffer

    def record(self, metric: str, **labels: str) -> None:
        if not metric.startswith("ott_identity_"):
            raise ValueError("identity metric must use the ott_identity_ prefix")
        safe = validate_labels(labels)
        self.metrics.increment(metric, **safe)
        self.events.emit({"event": metric, **safe})

    def alert(self, reason: str, *, component: str, lane: str) -> None:
        self.record(
            "ott_identity_alert_total",
            reason=reason,
            component=component,
            lane=lane,
            result="firing",
        )
