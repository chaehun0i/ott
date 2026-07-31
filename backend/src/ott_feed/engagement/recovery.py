"""Encrypted audit key archive and key-ID restore verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from base64 import b64decode, b64encode
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True, slots=True)
class RestoredKeyArchive:
    key_ids: frozenset[str]
    keys: Mapping[str, bytes]
    created_at: str
    retention_days: int


def create_key_archive(keys: Mapping[str, bytes], wrapping_key: bytes) -> bytes:
    if len(wrapping_key) not in {16, 24, 32} or not keys:
        raise ValueError("valid wrapping key and audit keys are required")
    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "retention_days": 400,
        "keys": {key_id: b64encode(value).decode() for key_id, value in sorted(keys.items())},
    }
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    manifest = {
        "payload": b64encode(canonical).decode(),
        "checksum": hashlib.sha256(canonical).hexdigest(),
        "signature": hmac.new(wrapping_key, canonical, hashlib.sha256).hexdigest(),
    }
    plaintext = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode()
    nonce = os.urandom(12)
    return b"U06KEY1" + nonce + AESGCM(wrapping_key).encrypt(nonce, plaintext, b"u06-key-archive")


def restore_key_archive(archive: bytes, wrapping_key: bytes) -> RestoredKeyArchive:
    if not archive.startswith(b"U06KEY1"):
        raise ValueError("invalid key archive format")
    nonce, ciphertext = archive[7:19], archive[19:]
    manifest = json.loads(
        AESGCM(wrapping_key).decrypt(nonce, ciphertext, b"u06-key-archive").decode()
    )
    canonical = b64decode(manifest["payload"])
    if hashlib.sha256(canonical).hexdigest() != manifest["checksum"]:
        raise ValueError("key archive checksum mismatch")
    expected = hmac.new(wrapping_key, canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, manifest["signature"]):
        raise ValueError("key archive manifest signature mismatch")
    payload = json.loads(canonical)
    keys = {key_id: b64decode(value) for key_id, value in payload["keys"].items()}
    return RestoredKeyArchive(
        frozenset(keys), keys, payload["created_at"], int(payload["retention_days"])
    )
