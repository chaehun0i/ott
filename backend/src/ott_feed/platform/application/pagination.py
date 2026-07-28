"""Opaque, signed cursor encoding and validation."""

import base64
import hashlib
import hmac
import json
from typing import Any

from ott_feed.platform.domain.errors import PlatformError
from ott_feed.platform.domain.models import CursorToken


def filter_fingerprint(filters: dict[str, Any]) -> str:
    canonical = json.dumps(filters, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


class CursorCodec:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 16:
            raise ValueError("cursor secret must contain at least 16 bytes")
        self.secret = secret

    def encode(self, cursor: CursorToken) -> str:
        payload = json.dumps(
            {
                "p": cursor.position,
                "t": cursor.tie_breaker,
                "f": cursor.filter_fingerprint,
                "v": cursor.contract_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        signature = hmac.digest(self.secret, payload, "sha256")
        return base64.urlsafe_b64encode(payload + signature).decode().rstrip("=")

    def decode(self, token: str, expected_fingerprint: str) -> CursorToken:
        try:
            padded = token + "=" * (-len(token) % 4)
            raw = base64.urlsafe_b64decode(padded.encode())
            payload, signature = raw[:-32], raw[-32:]
            if not hmac.compare_digest(signature, hmac.digest(self.secret, payload, "sha256")):
                raise ValueError("signature")
            data = json.loads(payload)
            cursor = CursorToken(data["p"], data["t"], data["f"], data["v"])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise PlatformError("invalid_cursor", "Cursor is invalid", 400) from exc
        if cursor.filter_fingerprint != expected_fingerprint:
            raise PlatformError("cursor_filter_mismatch", "Cursor does not match filters", 400)
        return cursor
