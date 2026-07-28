from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.ingestion.application.quarantine import QuarantineService
from ott_feed.ingestion.application.revalidation import RevalidationService, RevalidationTrigger
from ott_feed.ingestion.domain.errors import ValidationClosureError
from ott_feed.ingestion.domain.models import DecisionState, ValidationDecision

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def failed() -> ValidationDecision:
    return ValidationDecision(
        "failed-decision",
        "run-1",
        "merged-1",
        "rules-v1",
        DecisionState.QUARANTINED,
        reason_codes=("VAL_LICENSE",),
    )


def passed() -> ValidationDecision:
    return ValidationDecision(
        "passed-decision",
        "run-2",
        "merged-1",
        "rules-v2",
        DecisionState.PASSED_PENDING_PUBLICATION,
        publication_key="key",
    )


def test_quarantine_opens_only_from_failed_validation_and_exposes_bounded_status() -> None:
    service = QuarantineService()
    quarantine = service.open(failed(), "q-1", NOW)
    status = service.status(quarantine)
    assert status.reason_codes == ("VAL_LICENSE",)
    assert not hasattr(status, "payload_body")
    with pytest.raises(ValidationClosureError):
        service.open(passed(), "q-2", NOW)


def test_quarantine_resolves_only_through_superseding_pass() -> None:
    service = QuarantineService()
    quarantine = service.open(failed(), "q-1", NOW)
    service.supersede(quarantine, passed(), NOW + timedelta(seconds=1))
    assert quarantine.resolved_at == NOW + timedelta(seconds=1)

    invalid = failed()
    with pytest.raises(ValidationClosureError):
        service.supersede(service.open(failed(), "q-2", NOW), invalid, NOW)


def test_revalidation_attempt_key_is_stable_and_version_sensitive() -> None:
    service = RevalidationService()
    values = {
        "quarantine_id": "q-1",
        "decision_id": "d-1",
        "target_rule_version": "rules-v2",
        "source_version": "source-v1",
        "trigger": RevalidationTrigger.RULE_CHANGE,
    }
    first = service.request(**values)  # type: ignore[arg-type]
    second = service.request(**values)  # type: ignore[arg-type]
    assert first.attempt_key == second.attempt_key
    changed = service.request(**{**values, "source_version": "source-v2"})  # type: ignore[arg-type]
    assert changed.attempt_key != first.attempt_key


def test_manual_retry_requires_authorized_actor() -> None:
    service = RevalidationService()
    with pytest.raises(PermissionError):
        service.request(
            quarantine_id="q",
            decision_id="d",
            target_rule_version="rules",
            source_version="source",
            trigger=RevalidationTrigger.MANUAL_RETRY,
        )
    request = service.request(
        quarantine_id="q",
        decision_id="d",
        target_rule_version="rules",
        source_version="source",
        trigger=RevalidationTrigger.MANUAL_RETRY,
        actor_reference="operator:pseudonym",
        actor_authorized=True,
    )
    assert request.actor_reference == "operator:pseudonym"
