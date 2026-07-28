"""Licensed raw-body expiration preserving minimum permitted evidence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from ott_feed.ingestion.domain.models import RawMetadataRecord


def expire_raw_body(record: RawMetadataRecord, at: datetime) -> RawMetadataRecord:
    if at < record.payload_expires_at or record.payload_body is None:
        return record
    return replace(record, payload_body=None)


def select_expiry_batch(
    records: tuple[RawMetadataRecord, ...], at: datetime, limit: int
) -> tuple[RawMetadataRecord, ...]:
    if limit <= 0:
        raise ValueError("retention batch must be positive")
    eligible = [
        record
        for record in records
        if record.payload_body is not None and record.payload_expires_at <= at
    ]
    eligible.sort(key=lambda item: (item.payload_expires_at, item.raw_record_id))
    return tuple(eligible[:limit])
