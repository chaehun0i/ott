"""Fail-closed U05 restore re-entry checks."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    schema_current: bool
    session_closure: bool
    policy_references: bool
    validation_closure: bool
    trace_private: bool
    u02_compatible: bool
    u03_compatible: bool
    u04_compatible: bool


def deterministic_reentry_allowed(snapshot: RecoverySnapshot) -> bool:
    return all(
        (
            snapshot.schema_current,
            snapshot.session_closure,
            snapshot.policy_references,
            snapshot.validation_closure,
            snapshot.trace_private,
            snapshot.u02_compatible,
            snapshot.u03_compatible,
            snapshot.u04_compatible,
        )
    )


def ai_activation_allowed(
    snapshot: RecoverySnapshot,
    *,
    endpoint_allowed: bool,
    credential_present: bool,
    price_configured: bool,
    evaluation_passed: bool,
) -> bool:
    return deterministic_reentry_allowed(snapshot) and all(
        (endpoint_allowed, credential_present, price_configured, evaluation_passed)
    )
