"""Ports that keep the U02 core independent from frameworks and providers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol
from uuid import UUID


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def __call__(self) -> UUID: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, envelope: str, password: str) -> bool: ...

    def needs_rehash(self, envelope: str) -> bool: ...


class SecretCryptography(Protocol):
    def blind_index(self, domain: str, value: str) -> tuple[int, bytes]: ...

    def encrypt(self, record_id: str, field: str, plaintext: str) -> Mapping[str, object]: ...

    def decrypt(self, record_id: str, field: str, envelope: Mapping[str, object]) -> str: ...

    def session_token(self) -> tuple[str, bytes]: ...

    def session_token_hmac(self, token: str) -> bytes: ...

    def request_pseudonym(self, user_id: UUID, request_id: str) -> str: ...


class OAuthIdentityProvider(Protocol):
    def authorization_url(self, state: str, nonce: str) -> str: ...

    def exchange(self, code: str, expected_nonce: str) -> Mapping[str, object]: ...


class EmailDelivery(Protocol):
    def send(self, template: str, recipient: str, variables: Mapping[str, str]) -> None: ...


class ExportStorage(Protocol):
    def put_encrypted(self, object_key: str, payload: bytes, expires_at: datetime) -> str: ...

    def get_once(self, reference: str) -> bytes: ...

    def delete(self, reference: str) -> None: ...


class CatalogReference(Protocol):
    def content_exists(self, content_id: str) -> bool: ...


class AuditPublisher(Protocol):
    def emit(self, event_code: str, fields: Mapping[str, str]) -> None: ...


class JobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: Mapping[str, object], lane: str) -> UUID: ...


class IdentityRepository(Protocol):
    def get_user(self, user_id: UUID) -> object | None: ...

    def find_user_by_email_index(self, version: int, index: bytes) -> object | None: ...

    def save_user(self, user: object, expected_version: int | None = None) -> None: ...


class SessionRepository(Protocol):
    def find_by_token_hmac(self, token_hmac: bytes) -> object | None: ...

    def save_session(self, session: object) -> None: ...

    def revoke_all(self, user_id: UUID, reason: str, at: datetime) -> int: ...


class AggregateRepository(Protocol):
    def get(self, key: object) -> object | None: ...

    def save(self, aggregate: object, expected_version: int | None = None) -> None: ...


class UnitOfWork(Protocol):
    identities: IdentityRepository
    sessions: SessionRepository
    profiles: AggregateRepository
    libraries: AggregateRepository
    consents: AggregateRepository
    behavior: AggregateRepository
    features: AggregateRepository
    data_rights: AggregateRepository
    jobs: JobPublisher

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


UnitOfWorkFactory = Callable[[], AbstractContextManager[UnitOfWork]]


class FeatureSnapshotConsumer(Protocol):
    def consume(self, snapshot: Mapping[str, object]) -> None: ...


class DeletionClosureProbe(Protocol):
    def remaining_categories(self, request_id: UUID) -> Sequence[str]: ...
