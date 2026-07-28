"""Deterministic raw-envelope codec and observation construction."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from ott_feed.ingestion.domain.models import RawMetadataRecord, TombstoneKind
from ott_feed.ingestion.ports import ProviderRecordEnvelope


@dataclass(frozen=True, slots=True)
class RawEnvelopeCodec:
    version: int = 1

    def encode(self, provider_id: str, envelope: ProviderRecordEnvelope) -> bytes:
        value = {
            "version": self.version,
            "provider_id": provider_id,
            "provider_record_id": envelope.provider_record_id,
            "retrieved_at": envelope.retrieved_at.isoformat(),
            "payload": base64.b64encode(envelope.payload).decode("ascii"),
            "digest": hashlib.sha256(envelope.payload).hexdigest(),
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

    def decode(self, value: bytes) -> tuple[str, ProviderRecordEnvelope, str]:
        try:
            payload = json.loads(value)
            if payload["version"] != self.version:
                raise ValueError("unsupported raw envelope version")
            body = base64.b64decode(payload["payload"], validate=True)
            digest = hashlib.sha256(body).hexdigest()
            if digest != payload["digest"]:
                raise ValueError("raw payload digest mismatch")
            envelope = ProviderRecordEnvelope(
                str(payload["provider_record_id"]),
                body,
                datetime.fromisoformat(payload["retrieved_at"]),
            )
            return str(payload["provider_id"]), envelope, digest
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid raw envelope") from exc


def tombstone_kind(payload: bytes) -> TombstoneKind | None:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError:
        return None
    marker = value.get("_tombstone") if isinstance(value, dict) else None
    if marker == "content":
        return TombstoneKind.CONTENT
    if marker == "availability":
        return TombstoneKind.AVAILABILITY
    return None


class RawObservationFactory:
    def create(
        self,
        *,
        raw_record_id: str,
        job_id: str,
        provider_id: str,
        policy_id: str,
        retention_seconds: int,
        envelope: ProviderRecordEnvelope,
    ) -> RawMetadataRecord:
        if retention_seconds <= 0:
            raise ValueError("raw retention must be positive")
        return RawMetadataRecord(
            raw_record_id=raw_record_id,
            job_id=job_id,
            provider_id=provider_id,
            provider_record_id=envelope.provider_record_id,
            retrieved_at=envelope.retrieved_at,
            payload_digest=hashlib.sha256(envelope.payload).hexdigest(),
            payload_body=envelope.payload,
            policy_id=policy_id,
            payload_expires_at=envelope.retrieved_at + timedelta(seconds=retention_seconds),
            tombstone_kind=tombstone_kind(envelope.payload),
        )
