import pytest

from ott_feed.ingestion.contracts import (
    ApprovedCatalogCommandMapper,
    ValidationPredicateContract,
)
from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import DecisionState, ValidationDecision


def test_u05_contract_exposes_only_pure_bounded_predicates() -> None:
    contract = ValidationPredicateContract(
        "u05-validation-v1", "rules-v1", ("title", "runtime"), ("movie", "series"), 360
    )
    payload = contract.public_dict()
    assert set(payload) == {
        "contract_version",
        "rule_version",
        "required_evidence_fields",
        "allowed_content_types",
        "max_runtime_minutes",
    }
    assert not {"raw", "payload", "provider_token", "quarantine"} & set(payload)


def test_u03_mapper_rejects_every_non_passed_state() -> None:
    mapper = ApprovedCatalogCommandMapper()
    for state in (
        DecisionState.QUARANTINED,
        DecisionState.PUBLISHED,
        DecisionState.WITHDRAWAL_PENDING,
        DecisionState.WITHDRAWN,
    ):
        decision = ValidationDecision(
            "decision",
            "run",
            "merged",
            "rules",
            state,
            reason_codes=("VAL_FAILED",) if state is DecisionState.QUARANTINED else (),
        )
        with pytest.raises(ValidationClosureError):
            mapper.map(decision)


def test_u03_mapper_preserves_immutable_decision_key() -> None:
    decision = ValidationDecision(
        "decision",
        "run",
        "merged",
        "rules",
        DecisionState.PASSED_PENDING_PUBLICATION,
        publication_key="key",
    )
    command = ApprovedCatalogCommandMapper().map(decision)
    assert (command.decision_id, command.publication_key, command.action) == (
        "decision",
        "key",
        "publish",
    )
