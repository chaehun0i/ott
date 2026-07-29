"""Privacy-safe U05 telemetry and cost values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

ALLOWED_ATTRIBUTES = frozenset(
    {
        "component",
        "operation",
        "outcome",
        "reason_code",
        "intent_version",
        "score_version",
        "rule_version",
        "model_version",
        "fallback_mode",
        "circuit_state",
        "locale",
    }
)


def safe_attributes(values: Mapping[str, str]) -> dict[str, str]:
    return {key: value[:120] for key, value in values.items() if key in ALLOWED_ATTRIBUTES}


@dataclass(frozen=True, slots=True)
class UsageMeasurement:
    model_version: str
    input_units: int
    output_units: int
    unit_price: float

    @property
    def estimated_cost(self) -> float:
        return (self.input_units + self.output_units) * self.unit_price
