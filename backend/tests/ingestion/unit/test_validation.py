from datetime import UTC, datetime

from ott_feed.ingestion.application.validation import (
    ValidationEngine,
    require_provenance,
    require_title,
)
from ott_feed.ingestion.domain.models import (
    DecisionState,
    MergedMetadata,
    SourceFieldCandidate,
    ValidationRuleVersion,
)

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def merged(with_title: bool = True) -> MergedMetadata:
    selected = (
        (SourceFieldCandidate("title.ko-KR", "제목", "provider", "n1", NOW, 1),)
        if with_title
        else ()
    )
    return MergedMetadata("m1", "c1", "merge-v1", ("n1",), selected, (), NOW)


def rules() -> ValidationRuleVersion:
    return ValidationRuleVersion(
        "rules-v1", ("VAL_SCHEMA_TITLE", "VAL_PROVENANCE"), "u03-v1", "u05-v1", NOW
    )


def test_all_mandatory_rules_must_pass() -> None:
    engine = ValidationEngine(
        {"VAL_SCHEMA_TITLE": require_title, "VAL_PROVENANCE": require_provenance}
    )
    results, decision = engine.evaluate(
        merged(), rules(), run_id="run", decision_id="decision", evaluated_at=NOW
    )
    assert all(result.outcome == "passed" for result in results)
    assert decision.state is DecisionState.PASSED_PENDING_PUBLICATION
    assert decision.publication_key is not None


def test_missing_or_failed_rule_is_quarantined() -> None:
    engine = ValidationEngine({"VAL_SCHEMA_TITLE": require_title})
    _, decision = engine.evaluate(
        merged(False), rules(), run_id="run", decision_id="decision", evaluated_at=NOW
    )
    assert decision.state is DecisionState.QUARANTINED
    assert decision.reason_codes == ("VAL_RULE_MISSING", "VAL_TITLE_MISSING")
