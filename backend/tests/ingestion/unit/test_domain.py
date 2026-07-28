from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.ingestion.domain.errors import IllegalTransition, ValidationClosureError
from ott_feed.ingestion.domain.models import (
    CanonicalIdentityCandidate,
    DecisionState,
    IdentityDecision,
    IngestionJob,
    JobStatus,
    ProviderPolicy,
    ProviderPolicyStatus,
    QuarantineRecord,
    QuarantineResolution,
    ValidationDecision,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_policy_window_and_version_are_explicit() -> None:
    policy = ProviderPolicy(
        "policy-1",
        "provider-1",
        1,
        ProviderPolicyStatus.ACTIVE,
        frozenset({"collect", "display"}),
        frozenset({"KR"}),
        86_400,
        3_600,
        NOW,
        NOW + timedelta(days=1),
    )
    assert policy.active_at(NOW)
    assert not policy.active_at(NOW + timedelta(days=1))


def test_job_transitions_reject_duplicate_claim_and_classify_partial_success() -> None:
    job = IngestionJob("job-1", "provider-1", "policy-1", None)
    assert job.claim("worker-1", NOW) == 1
    with pytest.raises(IllegalTransition):
        job.claim("worker-2", NOW)
    job.succeeded_count = 2
    job.quarantined_count = 1
    job.finish(NOW)
    assert job.status is JobStatus.PARTIALLY_SUCCEEDED


def test_ambiguous_identity_cannot_select_content() -> None:
    with pytest.raises(ValueError):
        CanonicalIdentityCandidate(
            "resolution-1",
            "normalized-1",
            "identity-v1",
            IdentityDecision.AMBIGUOUS,
            ("content-1", "content-2"),
            "content-1",
            "title",
        )


def test_validation_decision_requires_closed_failure_or_publication_key() -> None:
    with pytest.raises(ValidationClosureError):
        ValidationDecision("decision-1", "run-1", "merge-1", "rules-v1", DecisionState.QUARANTINED)
    decision = ValidationDecision(
        "decision-2",
        "run-2",
        "merge-2",
        "rules-v1",
        DecisionState.PASSED_PENDING_PUBLICATION,
        publication_key="publication-2",
    )
    decision.acknowledge(3, NOW)
    assert decision.state is DecisionState.PUBLISHED
    assert decision.catalog_version == 3


def test_quarantine_can_only_be_superseded_once() -> None:
    quarantine = QuarantineRecord("q-1", "decision-1", ("VAL_SCHEMA",), NOW)
    quarantine.supersede("decision-2", NOW + timedelta(seconds=1))
    assert quarantine.resolution is QuarantineResolution.SUPERSEDED_BY_PASS
    with pytest.raises(IllegalTransition):
        quarantine.supersede("decision-3", NOW + timedelta(seconds=2))
