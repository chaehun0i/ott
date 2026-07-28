"""Payload-free U04 telemetry allowlist."""

from __future__ import annotations

from collections.abc import Mapping

ALLOWED_ATTRIBUTES = frozenset(
    {
        "provider_id",
        "job_id",
        "attempt_id",
        "component",
        "operation",
        "outcome",
        "policy_version",
        "rule_version",
        "reason_family",
        "lane",
        "circuit_state",
    }
)


def safe_attributes(values: Mapping[str, str]) -> dict[str, str]:
    return {key: value[:120] for key, value in values.items() if key in ALLOWED_ATTRIBUTES}
