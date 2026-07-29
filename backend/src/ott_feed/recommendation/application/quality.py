"""Version activation comparison gate."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualityResult:
    hard_condition_rate: float
    catalog_closure_rate: float
    grounding_precision: float
    relevance: float


def activation_allowed(active: QualityResult, candidate: QualityResult) -> bool:
    safety = (
        candidate.hard_condition_rate == 1.0
        and candidate.catalog_closure_rate == 1.0
        and candidate.grounding_precision == 1.0
    )
    return safety and candidate.relevance >= 0.95 and candidate.relevance >= active.relevance
