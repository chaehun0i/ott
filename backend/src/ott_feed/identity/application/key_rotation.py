"""Checkpointed 500-row dual-read/new-write key rotation orchestration."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Protocol

from ott_feed.identity.domain.models import KeyRotationProgress


class RotationProgressRepository(Protocol):
    def get(self, from_version: int, to_version: int) -> KeyRotationProgress | None: ...

    def save(self, progress: KeyRotationProgress) -> None: ...


class ReencryptableStore(Protocol):
    def fetch_batch(
        self, from_version: int, cursor: str | None, limit: int
    ) -> Sequence[tuple[str, str, str]]: ...

    def reencrypt(self, record_id: str, field: str, plaintext: str, to_version: int) -> None: ...

    def old_version_count(self, version: int) -> int: ...


class KeyRotationService:
    def __init__(
        self,
        progress_repository: RotationProgressRepository,
        store: ReencryptableStore,
        now: Callable[[], datetime],
        batch_size: int = 500,
    ) -> None:
        if batch_size != 500:
            raise ValueError("U02 key rotation batch size must be 500")
        self.progress_repository = progress_repository
        self.store = store
        self.now = now
        self.batch_size = batch_size

    def run_batch(self, from_version: int, to_version: int) -> KeyRotationProgress:
        progress = self.progress_repository.get(from_version, to_version) or KeyRotationProgress(
            from_version, to_version
        )
        batch = self.store.fetch_batch(from_version, progress.cursor, self.batch_size)
        failed = 0
        last_cursor = progress.cursor or ""
        for record_id, field, plaintext in batch:
            last_cursor = record_id
            try:
                self.store.reencrypt(record_id, field, plaintext, to_version)
            except Exception:
                failed += 1
        progress.checkpoint(last_cursor, len(batch) - failed, failed)
        if len(batch) < self.batch_size and failed == 0:
            progress.complete(self.now(), self.store.old_version_count(from_version))
        self.progress_repository.save(progress)
        return progress
