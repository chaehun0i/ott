"""Structured JSON logging with deterministic sensitive-field redaction."""

import json
import logging
from collections import Counter, deque
from threading import Lock
from typing import Any

SENSITIVE_FRAGMENTS = ("password", "secret", "token", "credential", "authorization", "cookie")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if any(fragment in key.lower() for fragment in SENSITIVE_FRAGMENTS)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(redact(fields))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class Metrics:
    def __init__(self) -> None:
        self._counts: Counter[tuple[str, tuple[tuple[str, str], ...]]] = Counter()
        self._lock = Lock()

    def increment(self, name: str, **labels: str) -> None:
        with self._lock:
            self._counts[(name, tuple(sorted(labels.items())))] += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                f"{name}{dict(labels)}": count for (name, labels), count in self._counts.items()
            }


class NonBlockingTelemetryBuffer:
    """Bounded local fallback; full buffers drop oldest telemetry, never business requests."""

    def __init__(self, capacity: int = 1000) -> None:
        self._items: deque[dict[str, Any]] = deque(maxlen=capacity)
        self.dropped = 0

    def emit(self, event: dict[str, Any]) -> None:
        if len(self._items) == self._items.maxlen:
            self.dropped += 1
        self._items.append(redact(event))

    def drain(self) -> list[dict[str, Any]]:
        items = list(self._items)
        self._items.clear()
        return items
