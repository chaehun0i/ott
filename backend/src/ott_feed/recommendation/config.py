"""Validated U05 runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class RecommendationSettings:
    total_timeout_ms: int = 10_000
    intent_timeout_ms: int = 2_750
    draft_timeout_ms: int = 4_250
    ai_concurrency: int = 4
    ai_queue_timeout_ms: int = 100
    max_input_bytes: int = 4_096
    max_conditions: int = 32
    max_candidates: int = 1_000
    max_scored: int = 500
    max_reserve: int = 100
    max_exposed: int = 20
    max_claims_per_item: int = 64
    max_ai_response_bytes: int = 262_144
    daily_ai_units: int = 100_000

    def __post_init__(self) -> None:
        for field in fields(self):
            name = field.name
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.intent_timeout_ms + self.draft_timeout_ms >= self.total_timeout_ms:
            raise ValueError("AI stages must leave non-AI deadline capacity")
        if not self.max_exposed <= self.max_reserve <= self.max_scored <= self.max_candidates:
            raise ValueError("candidate bounds must be monotonic")

    @classmethod
    def from_environment(cls) -> RecommendationSettings:
        return cls(
            total_timeout_ms=_positive_int("U05_TOTAL_TIMEOUT_MS", 10_000),
            intent_timeout_ms=_positive_int("U05_INTENT_TIMEOUT_MS", 2_750),
            draft_timeout_ms=_positive_int("U05_DRAFT_TIMEOUT_MS", 4_250),
            ai_concurrency=_positive_int("U05_AI_CONCURRENCY", 4),
            ai_queue_timeout_ms=_positive_int("U05_AI_QUEUE_TIMEOUT_MS", 100),
            max_input_bytes=_positive_int("U05_MAX_INPUT_BYTES", 4_096),
            max_conditions=_positive_int("U05_MAX_CONDITIONS", 32),
            max_candidates=_positive_int("U05_MAX_CANDIDATES", 1_000),
            max_scored=_positive_int("U05_MAX_SCORED", 500),
            max_reserve=_positive_int("U05_MAX_RESERVE", 100),
            max_exposed=_positive_int("U05_MAX_EXPOSED", 20),
            max_claims_per_item=_positive_int("U05_MAX_CLAIMS_PER_ITEM", 64),
            max_ai_response_bytes=_positive_int("U05_MAX_AI_RESPONSE_BYTES", 262_144),
            daily_ai_units=_positive_int("U05_DAILY_AI_UNITS", 100_000),
        )
