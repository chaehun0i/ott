"""Minimal versioned U05 validation contract and safe U03 command mapper."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import DecisionState, ValidationDecision


@dataclass(frozen=True, slots=True)
class ValidationPredicateContract:
    contract_version: str
    rule_version: str
    required_evidence_fields: tuple[str, ...]
    allowed_content_types: tuple[str, ...]
    max_runtime_minutes: int

    def __post_init__(self) -> None:
        if not self.contract_version or not self.rule_version:
            raise ValueError("contract and rule versions are required")
        if self.max_runtime_minutes <= 0:
            raise ValueError("runtime bound must be positive")

    def public_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApprovedCatalogCommand:
    decision_id: str
    publication_key: str
    merged_id: str
    action: str


class ApprovedCatalogCommandMapper:
    def map(
        self, decision: ValidationDecision, *, action: str = "publish"
    ) -> ApprovedCatalogCommand:
        if (
            decision.state is not DecisionState.PASSED_PENDING_PUBLICATION
            or decision.publication_key is None
        ):
            raise ValidationClosureError("only a passed pending decision can publish")
        if action not in {"publish", "replace", "withdraw", "reactivate"}:
            raise ValueError("unsupported catalog action")
        return ApprovedCatalogCommand(
            decision.decision_id, decision.publication_key, decision.merged_id, action
        )
