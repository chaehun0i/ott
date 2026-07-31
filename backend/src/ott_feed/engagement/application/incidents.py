"""Alert normalization and optimistic incident lifecycle."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from enum import StrEnum


class IncidentState(StrEnum):
    OPEN = "open"
    MITIGATING = "mitigating"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


def correlation_key(service: str, symptom: str, scope: str) -> str:
    return hashlib.sha256(f"{service}\x1f{symptom}\x1f{scope}".encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    correlation_key: str
    severity: str
    state: IncidentState = IncidentState.OPEN
    version: int = 0
    occurrences: int = 1
    owner: str | None = None
    recovery_evidence: str | None = None
    coe_reference: str | None = None

    def transition(
        self, target: IncidentState, expected_version: int, evidence: str = ""
    ) -> Incident:
        if expected_version != self.version:
            raise ValueError("incident version conflict")
        allowed = {
            IncidentState.OPEN: {IncidentState.MITIGATING},
            IncidentState.MITIGATING: {IncidentState.MONITORING},
            IncidentState.MONITORING: {IncidentState.MITIGATING, IncidentState.RESOLVED},
            IncidentState.RESOLVED: set(),
        }
        if target not in allowed[self.state]:
            raise ValueError("invalid incident transition")
        if target is IncidentState.RESOLVED and (not self.owner or not evidence):
            raise ValueError("resolution requires owner and recovery evidence")
        return replace(
            self,
            state=target,
            version=self.version + 1,
            recovery_evidence=evidence or self.recovery_evidence,
        )

    def recur(self) -> Incident:
        target = IncidentState.MITIGATING if self.state is IncidentState.MONITORING else self.state
        return replace(
            self, state=target, version=self.version + 1, occurrences=self.occurrences + 1
        )
