"""Complete, versioned and fail-closed metadata validation."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from datetime import datetime

from ott_feed.ingestion.domain.models import (
    DecisionState,
    MergedMetadata,
    RuleOutcome,
    RuleResult,
    ValidationDecision,
    ValidationRuleVersion,
)

ValidationRule = Callable[[MergedMetadata, datetime], RuleResult]


class ValidationEngine:
    def __init__(self, rules: Mapping[str, ValidationRule]) -> None:
        self.rules = rules

    def evaluate(
        self,
        value: MergedMetadata,
        rule_version: ValidationRuleVersion,
        *,
        run_id: str,
        decision_id: str,
        evaluated_at: datetime,
    ) -> tuple[tuple[RuleResult, ...], ValidationDecision]:
        results: list[RuleResult] = []
        for rule_id in rule_version.mandatory_rule_ids:
            rule = self.rules.get(rule_id)
            if rule is None:
                results.append(RuleResult(rule_id, RuleOutcome.ERROR, "VAL_RULE_MISSING"))
                continue
            try:
                result = rule(value, evaluated_at)
            except Exception:
                result = RuleResult(rule_id, RuleOutcome.ERROR, "VAL_RULE_ERROR")
            if result.rule_id != rule_id:
                result = RuleResult(rule_id, RuleOutcome.ERROR, "VAL_RULE_ID_MISMATCH")
            results.append(result)
        failures = tuple(
            sorted(
                {
                    result.reason_code or f"VAL_{result.outcome.value.upper()}"
                    for result in results
                    if result.outcome is not RuleOutcome.PASSED
                }
            )
        )
        if failures:
            decision = ValidationDecision(
                decision_id,
                run_id,
                value.merged_id,
                rule_version.version,
                DecisionState.QUARANTINED,
                reason_codes=failures,
            )
        else:
            key_material = f"{decision_id}\x1f{value.merged_id}\x1f{rule_version.version}"
            publication_key = hashlib.sha256(key_material.encode()).hexdigest()
            decision = ValidationDecision(
                decision_id,
                run_id,
                value.merged_id,
                rule_version.version,
                DecisionState.PASSED_PENDING_PUBLICATION,
                publication_key=publication_key,
            )
        return tuple(results), decision


def require_title(value: MergedMetadata, _: datetime) -> RuleResult:
    passed = any(
        candidate.path.startswith("title.") and candidate.value
        for candidate in value.selected_fields
    )
    return RuleResult(
        "VAL_SCHEMA_TITLE",
        RuleOutcome.PASSED if passed else RuleOutcome.FAILED,
        None if passed else "VAL_TITLE_MISSING",
    )


def require_provenance(value: MergedMetadata, _: datetime) -> RuleResult:
    passed = all(
        candidate.provider_id and candidate.normalized_id for candidate in value.selected_fields
    )
    return RuleResult(
        "VAL_PROVENANCE",
        RuleOutcome.PASSED if passed and value.selected_fields else RuleOutcome.FAILED,
        None if passed and value.selected_fields else "VAL_PROVENANCE_MISSING",
    )
