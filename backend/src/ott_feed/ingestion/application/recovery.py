"""Fail-closed U04 restore verification and service re-entry."""

from __future__ import annotations

from dataclasses import dataclass

from ott_feed.ingestion.domain.errors import IngestionError


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    missing_policy_references: int = 0
    missing_rule_references: int = 0
    cursor_regressions: int = 0
    duplicate_publication_receipts: int = 0
    quarantine_leaks: int = 0
    expired_raw_bodies: int = 0
    pending_publications_reconciled: bool = False


@dataclass(frozen=True, slots=True)
class ReentryDecision:
    publication_enabled: bool
    provider_claims_enabled: bool
    checks: tuple[str, ...]


class RecoveryCoordinator:
    def verify(self, snapshot: RecoverySnapshot) -> ReentryDecision:
        violations = tuple(
            name
            for name, value in (
                ("missing_policy_references", snapshot.missing_policy_references),
                ("missing_rule_references", snapshot.missing_rule_references),
                ("cursor_regressions", snapshot.cursor_regressions),
                ("duplicate_publication_receipts", snapshot.duplicate_publication_receipts),
                ("quarantine_leaks", snapshot.quarantine_leaks),
                ("expired_raw_bodies", snapshot.expired_raw_bodies),
            )
            if value != 0
        )
        if violations:
            raise IngestionError(
                "U04_RECOVERY_INVARIANT_FAILED",
                f"restore re-entry blocked: {','.join(violations)}",
            )
        return ReentryDecision(
            publication_enabled=True,
            provider_claims_enabled=snapshot.pending_publications_reconciled,
            checks=(
                "policy_references",
                "rule_references",
                "cursor_monotonicity",
                "receipt_uniqueness",
                "quarantine_closure",
                "retention_enforced",
                "publication_reconciliation",
            ),
        )
