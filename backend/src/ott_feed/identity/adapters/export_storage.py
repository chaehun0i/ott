"""Encrypted one-time export storage behind a provider-neutral object client."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ott_feed.identity.domain.errors import denied


class PrivateObjectClient(Protocol):
    def put(self, object_key: str, payload: bytes, expires_at: datetime) -> None: ...

    def get(self, object_key: str) -> bytes: ...

    def delete(self, object_key: str) -> None: ...


class EncryptedExportStorage:
    def __init__(self, client: PrivateObjectClient, key: bytes) -> None:
        self.client = client
        self._key = hashlib.sha256(b"u02:export:" + key).digest()

    def put_encrypted(self, object_key: str, payload: bytes, expires_at: datetime) -> str:
        nonce = secrets.token_bytes(12)
        aad = object_key.encode()
        encrypted = nonce + AESGCM(self._key).encrypt(nonce, payload, aad)
        self.client.put(object_key, encrypted, expires_at)
        return object_key

    def get_once(self, reference: str) -> bytes:
        encrypted = self.client.get(reference)
        try:
            payload = AESGCM(self._key).decrypt(encrypted[:12], encrypted[12:], reference.encode())
        except (InvalidTag, ValueError) as exc:
            raise denied("export_integrity_failure", "identity.export_unavailable") from exc
        self.client.delete(reference)
        return payload

    def delete(self, reference: str) -> None:
        self.client.delete(reference)


class InMemoryPrivateObjectClient:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, datetime]] = {}

    def put(self, object_key: str, payload: bytes, expires_at: datetime) -> None:
        self.objects[object_key] = (payload, expires_at)

    def get(self, object_key: str) -> bytes:
        try:
            payload, _ = self.objects[object_key]
            return payload
        except KeyError as exc:
            raise denied("export_not_found", "identity.export_unavailable") from exc

    def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)
