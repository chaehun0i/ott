"""Maintained-library security adapters for passwords, sessions, CSRF and field encryption."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import BoundedSemaphore
from typing import TypeVar
from urllib.parse import urlparse
from uuid import UUID

from argon2 import PasswordHasher as Argon2LibraryHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ott_feed.identity.domain.errors import denied, invalid, unavailable

T = TypeVar("T")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


@dataclass(frozen=True, slots=True)
class Argon2Policy:
    memory_kib: int = 65536
    time_cost: int = 3
    parallelism: int = 1
    hash_len: int = 32
    salt_len: int = 16
    version: int = 1

    def __post_init__(self) -> None:
        if self.memory_kib < 65536 or min(self.time_cost, self.parallelism) < 1:
            raise ValueError("Argon2 policy is below the approved baseline")


class BoundedArgon2PasswordHasher:
    def __init__(self, policy: Argon2Policy, concurrency: int = 2) -> None:
        if concurrency < 1:
            raise ValueError("Argon2 concurrency must be positive")
        self.policy = policy
        self._hasher = Argon2LibraryHasher(
            time_cost=policy.time_cost,
            memory_cost=policy.memory_kib,
            parallelism=policy.parallelism,
            hash_len=policy.hash_len,
            salt_len=policy.salt_len,
            type=Type.ID,
        )
        self._semaphore = BoundedSemaphore(concurrency)
        self._executor = ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="argon2")

    def _run(self, operation: Callable[[], T]) -> T:
        if not self._semaphore.acquire(blocking=False):
            raise unavailable("password_hasher_saturated", "identity.try_again")
        try:
            return self._executor.submit(operation).result()
        finally:
            self._semaphore.release()

    def hash(self, password: str) -> str:
        return self._run(lambda: self._hasher.hash(password))

    def verify(self, envelope: str, password: str) -> bool:
        try:
            return self._run(lambda: self._hasher.verify(envelope, password))
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    def needs_rehash(self, envelope: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(envelope)
        except InvalidHashError:
            return True

    def benchmark(self, password: str = "benchmark-only-password") -> float:
        started = time.perf_counter()
        self.hash(password)
        return (time.perf_counter() - started) * 1000

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)


class EnvelopeCryptography:
    def __init__(
        self,
        key_version: int,
        kek: bytes,
        blind_index_key: bytes,
        session_pepper: bytes,
    ) -> None:
        if key_version < 1:
            raise ValueError("key version must be positive")
        self.key_version = key_version
        self._kek = hashlib.sha256(b"u02:kek:" + kek).digest()
        self._blind_key = hashlib.sha256(b"u02:blind:" + blind_index_key).digest()
        self._session_key = hashlib.sha256(b"u02:session:" + session_pepper).digest()

    def blind_index(self, domain: str, value: str) -> tuple[int, bytes]:
        if not domain or not value:
            raise invalid("blind_index_input", "identity.security_input_invalid")
        payload = domain.encode() + b"\x00" + value.encode()
        return self.key_version, hmac.digest(self._blind_key, payload, "sha256")

    def encrypt(self, record_id: str, field: str, plaintext: str) -> dict[str, object]:
        if not record_id or not field:
            raise invalid("encryption_context", "identity.security_input_invalid")
        dek = AESGCM.generate_key(bit_length=256)
        data_nonce = secrets.token_bytes(12)
        wrap_nonce = secrets.token_bytes(12)
        associated_data = self._aad(record_id, field)
        ciphertext = AESGCM(dek).encrypt(data_nonce, plaintext.encode(), associated_data)
        wrapped_dek = AESGCM(self._kek).encrypt(wrap_nonce, dek, associated_data)
        return {
            "algorithm": "AES-256-GCM",
            "keyVersion": self.key_version,
            "nonce": _b64encode(data_nonce),
            "ciphertext": _b64encode(ciphertext),
            "wrapNonce": _b64encode(wrap_nonce),
            "wrappedDek": _b64encode(wrapped_dek),
        }

    def decrypt(self, record_id: str, field: str, envelope: Mapping[str, object]) -> str:
        try:
            if envelope["algorithm"] != "AES-256-GCM":
                raise ValueError("unsupported algorithm")
            associated_data = self._aad(record_id, field)
            wrap_nonce = _b64decode(str(envelope["wrapNonce"]))
            wrapped_dek = _b64decode(str(envelope["wrappedDek"]))
            dek = AESGCM(self._kek).decrypt(wrap_nonce, wrapped_dek, associated_data)
            nonce = _b64decode(str(envelope["nonce"]))
            ciphertext = _b64decode(str(envelope["ciphertext"]))
            return AESGCM(dek).decrypt(nonce, ciphertext, associated_data).decode()
        except (InvalidTag, KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            raise denied("ciphertext_integrity_failure", "identity.data_unavailable") from exc

    def session_token(self) -> tuple[str, bytes]:
        token = _b64encode(secrets.token_bytes(32))
        return token, self.session_token_hmac(token)

    def session_token_hmac(self, token: str) -> bytes:
        return hmac.digest(self._session_key, b"lookup\x00" + token.encode(), "sha256")

    def request_pseudonym(self, user_id: UUID, request_id: str) -> str:
        payload = b"request-subject\x00" + user_id.bytes + b"\x00" + request_id.encode()
        return _b64encode(hmac.digest(self._session_key, payload, "sha256"))

    @staticmethod
    def _aad(record_id: str, field: str) -> bytes:
        return json.dumps(
            {"schema": 1, "record": record_id, "field": field},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()


class CsrfProtector:
    def __init__(self, signing_key: bytes, allowed_origins: frozenset[str]) -> None:
        if not signing_key or not allowed_origins:
            raise ValueError("CSRF signing key and allowed origins are required")
        self._key = hashlib.sha256(b"u02:csrf:" + signing_key).digest()
        self._origins = frozenset(origin.rstrip("/") for origin in allowed_origins)

    def issue(self) -> str:
        nonce = _b64encode(secrets.token_bytes(32))
        signature = _b64encode(hmac.digest(self._key, nonce.encode(), "sha256"))
        return f"{nonce}.{signature}"

    def verify(
        self, cookie_token: str | None, header_token: str | None, origin: str | None
    ) -> None:
        if (
            not cookie_token
            or not header_token
            or not hmac.compare_digest(cookie_token, header_token)
        ):
            raise denied("csrf_token_invalid", "identity.csrf_invalid")
        try:
            nonce, signature = cookie_token.split(".", 1)
            expected = _b64encode(hmac.digest(self._key, nonce.encode(), "sha256"))
        except ValueError as exc:
            raise denied("csrf_token_invalid", "identity.csrf_invalid") from exc
        if not hmac.compare_digest(signature, expected):
            raise denied("csrf_token_invalid", "identity.csrf_invalid")
        normalized_origin = self._normalize_origin(origin)
        if normalized_origin not in self._origins:
            raise denied("csrf_origin_invalid", "identity.csrf_invalid")

    @staticmethod
    def _normalize_origin(origin: str | None) -> str:
        if not origin:
            return ""
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}"
