"""Deterministic cursor/page checkpoint helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CursorCheckpoint:
    provider_id: str
    start_cursor: str | None
    next_cursor: str | None
    record_ids: tuple[str, ...]

    @property
    def page_digest(self) -> str:
        canonical = "\x1f".join(
            (
                self.provider_id,
                self.start_cursor or "",
                self.next_cursor or "",
                *sorted(self.record_ids),
            )
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def replay_start(durable_cursor: str | None, configured_start: str | None) -> str | None:
    return durable_cursor if durable_cursor is not None else configured_start
