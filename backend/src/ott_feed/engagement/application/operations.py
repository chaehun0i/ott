"""Privileged overrides, audit integrity and trace projection."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta

ALLOWED_OVERRIDE_FIELDS = frozenset({"visibility", "title", "synopsis", "age_rating"})
ALLOWED_TRACE_FIELDS = frozenset({"request_id", "policy_versions", "reason_codes", "outcome"})


@dataclass(frozen=True, slots=True)
class OverrideCommand:
    operation_id: str
    content_id: str
    expected_version: int
    patch: Mapping[str, object]
    actor_ref: str
    authenticated_at: datetime
    idempotency_key: str

    def validate(self, now: datetime) -> None:
        if self.expected_version < 0 or not self.idempotency_key:
            raise ValueError("version and idempotency key are required")
        if now - self.authenticated_at > timedelta(minutes=15):
            raise PermissionError("recent authentication required")
        if not self.patch or not set(self.patch).issubset(ALLOWED_OVERRIDE_FIELDS):
            raise ValueError("override contains a prohibited field")


def canonical_audit_bytes(event: Mapping[str, object], schema_version: int = 1) -> bytes:
    allowed = {
        "event_id",
        "occurred_at",
        "actor_ref",
        "operation",
        "outcome",
        "target_ref",
        "correlation_id",
    }
    projected = {key: event[key] for key in sorted(event) if key in allowed}
    return (
        b"ott-feed:u06:audit\x00"
        + str(schema_version).encode()
        + b"\x00"
        + json.dumps(projected, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    )


@dataclass(frozen=True, slots=True)
class AuditKeyRing:
    current_key_id: str
    keys: Mapping[str, bytes]

    def sign(self, event: Mapping[str, object]) -> tuple[str, str]:
        key = self.keys.get(self.current_key_id)
        if not key:
            raise ValueError("current audit key is missing")
        digest = hmac.new(key, canonical_audit_bytes(event), hashlib.sha256).hexdigest()
        return self.current_key_id, digest

    def verify(self, event: Mapping[str, object], key_id: str, digest: str) -> bool:
        key = self.keys.get(key_id)
        if not key:
            return False
        expected = hmac.new(key, canonical_audit_bytes(event), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, digest)


def project_trace(trace: Mapping[str, object], limit: int = 100) -> dict[str, object]:
    if not 1 <= limit <= 100:
        raise ValueError("trace limit must be between 1 and 100")
    result = {key: trace[key] for key in ALLOWED_TRACE_FIELDS if key in trace}
    reason_codes = result.get("reason_codes")
    if isinstance(reason_codes, list):
        result["reason_codes"] = reason_codes[:limit]
    return result
