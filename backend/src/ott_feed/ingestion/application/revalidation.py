"""Idempotent source/rule/manual revalidation commands."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum


class RevalidationTrigger(StrEnum):
    SOURCE_CHANGE = "source_change"
    RULE_CHANGE = "rule_change"
    MANUAL_RETRY = "manual_retry"


@dataclass(frozen=True, slots=True)
class RevalidationRequest:
    attempt_key: str
    quarantine_id: str
    decision_id: str
    target_rule_version: str
    trigger: RevalidationTrigger
    actor_reference: str | None


class RevalidationService:
    def request(
        self,
        *,
        quarantine_id: str,
        decision_id: str,
        target_rule_version: str,
        source_version: str,
        trigger: RevalidationTrigger,
        actor_reference: str | None = None,
        actor_authorized: bool = False,
    ) -> RevalidationRequest:
        if trigger is RevalidationTrigger.MANUAL_RETRY and (
            not actor_authorized or not actor_reference
        ):
            raise PermissionError("manual revalidation requires an authorized actor")
        if trigger is not RevalidationTrigger.MANUAL_RETRY and actor_reference is not None:
            raise ValueError("automated revalidation cannot carry an actor reference")
        material = "\x1f".join(
            (quarantine_id, decision_id, target_rule_version, source_version, trigger.value)
        )
        attempt_key = hashlib.sha256(material.encode()).hexdigest()
        return RevalidationRequest(
            attempt_key,
            quarantine_id,
            decision_id,
            target_rule_version,
            trigger,
            actor_reference,
        )
