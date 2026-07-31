"""Bounded retention and recovery closure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RetainedRecord:
    record_id: str
    expires_at: datetime
    legal_hold: bool = False


def expired_batch(
    records: tuple[RetainedRecord, ...], now: datetime, limit: int = 500
) -> tuple[RetainedRecord, ...]:
    if not 1 <= limit <= 500:
        raise ValueError("retention limit must be between 1 and 500")
    eligible = (item for item in records if not item.legal_hold and item.expires_at <= now)
    return tuple(sorted(eligible, key=lambda item: (item.expires_at, item.record_id))[:limit])


def verify_recovery_key_ids(database_key_ids: set[str], archive_key_ids: set[str]) -> None:
    missing = database_key_ids - archive_key_ids
    if missing:
        raise ValueError(f"missing audit key ids: {','.join(sorted(missing))}")
