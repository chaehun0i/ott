"""Idempotency registry application service."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from ott_feed.platform.domain.errors import conflict
from ott_feed.platform.domain.models import IdempotencyRecord, IdempotencyStatus


class IdempotencyRepository(Protocol):
    def get(self, scope: str, key: str) -> IdempotencyRecord | None: ...

    def add(self, record: IdempotencyRecord) -> None: ...

    def save(self, record: IdempotencyRecord) -> None: ...


class MemoryIdempotencyRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], IdempotencyRecord] = {}

    def get(self, scope: str, key: str) -> IdempotencyRecord | None:
        return self.records.get((scope, key))

    def add(self, record: IdempotencyRecord) -> None:
        identity = (record.scope, record.key)
        if identity in self.records:
            raise conflict("idempotency_key_exists", "Idempotency key already exists")
        self.records[identity] = record

    def save(self, record: IdempotencyRecord) -> None:
        self.records[(record.scope, record.key)] = record


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


class IdempotencyService:
    def __init__(self, repository: IdempotencyRepository) -> None:
        self.repository = repository

    def reserve(self, scope: str, key: str, payload: dict[str, Any]) -> IdempotencyRecord:
        digest = payload_hash(payload)
        existing = self.repository.get(scope, key)
        if existing is not None:
            existing.assert_payload(digest)
            if existing.status == IdempotencyStatus.RESERVED:
                raise conflict("idempotency_in_progress", "Request is already in progress")
            return existing
        record = IdempotencyRecord(scope, key, digest)
        self.repository.add(record)
        return record

    def complete(self, record: IdempotencyRecord, status: int, body: dict[str, Any]) -> None:
        record.complete(status, body)
        self.repository.save(record)
