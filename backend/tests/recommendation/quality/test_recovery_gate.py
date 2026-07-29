from ott_feed.recommendation.application.recovery import (
    RecoverySnapshot,
    ai_activation_allowed,
    deterministic_reentry_allowed,
)
from ott_feed.recommendation.application.retention import plan_retention
from ott_feed.recommendation.maintenance import run


def healthy() -> RecoverySnapshot:
    return RecoverySnapshot(True, True, True, True, True, True, True, True)


def test_retention_is_bounded_and_checkpointed() -> None:
    batch = plan_retention(tuple(str(index) for index in range(600)))
    assert len(batch.ids) == 500 and batch.next_cursor == "499"


def test_reentry_is_deterministic_first_and_ai_is_separate() -> None:
    assert deterministic_reentry_allowed(healthy())
    assert not ai_activation_allowed(
        healthy(),
        endpoint_allowed=True,
        credential_present=True,
        price_configured=True,
        evaluation_passed=False,
    )


def test_maintenance_command_is_bounded() -> None:
    assert run(["retention", "--limit", "500"]) == 0
