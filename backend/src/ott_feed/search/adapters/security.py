"""Purpose-separated HMAC cursors and keyed query fingerprints."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import asdict
from pathlib import Path

from ott_feed.catalog.domain.models import FeedCursor
from ott_feed.search.domain.errors import CursorError


def _read_key(path: str) -> bytes:
    key = Path(path).read_bytes().strip()
    if len(key) < 32:
        raise ValueError("HMAC keys must contain at least 32 bytes")
    return key


class CursorSigner:
    def __init__(self, current_key: bytes, previous_key: bytes | None = None) -> None:
        if len(current_key) < 32 or (previous_key is not None and len(previous_key) < 32):
            raise ValueError("HMAC keys must contain at least 32 bytes")
        self.current_key = current_key
        self.previous_key = previous_key

    @classmethod
    def from_files(cls, current_file: str, previous_file: str = "") -> CursorSigner:
        return cls(_read_key(current_file), _read_key(previous_file) if previous_file else None)

    def encode(self, cursor: FeedCursor) -> str:
        payload = json.dumps(asdict(cursor), separators=(",", ":"), sort_keys=True).encode()
        signature = hmac.digest(self.current_key, b"cursor:v1:" + payload, "sha256")
        payload_token = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        signature_token = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{payload_token}.{signature_token}"

    def decode(self, token: str) -> FeedCursor:
        try:
            payload_token, signature_token = token.split(".", 1)
            payload = base64.urlsafe_b64decode(payload_token + "=" * (-len(payload_token) % 4))
            signature = base64.urlsafe_b64decode(
                signature_token + "=" * (-len(signature_token) % 4)
            )
            valid = any(
                hmac.compare_digest(
                    signature,
                    hmac.digest(key, b"cursor:v1:" + payload, "sha256"),
                )
                for key in (self.current_key, self.previous_key)
                if key is not None
            )
            if not valid:
                raise CursorError()
            value = json.loads(payload)
            return FeedCursor(
                fingerprint=str(value["fingerprint"]),
                generation=str(value["generation"]),
                score=float(value["score"]),
                content_id=str(value["content_id"]),
            )
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CursorError() from exc

    def fingerprint(self, canonical_query: str) -> str:
        return hmac.new(
            self.current_key,
            b"fingerprint:v1:" + canonical_query.encode(),
            hashlib.sha256,
        ).hexdigest()
