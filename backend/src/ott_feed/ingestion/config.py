"""Typed U04 operational configuration with fail-fast bounds."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _positive_float(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _ratio(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if not 0 < value <= 1:
        raise ValueError(f"{name} must be within (0, 1]")
    return value


@dataclass(frozen=True, slots=True)
class IngestionSettings:
    worker_pool_size: int = 5
    api_pool_size: int = 2
    claim_batch_size: int = 100
    global_provider_concurrency: int = 4
    per_provider_concurrency: int = 1
    publication_concurrency: int = 1
    retention_concurrency: int = 1
    connect_timeout_seconds: float = 0.3
    read_timeout_seconds: float = 4.0
    total_timeout_seconds: float = 5.0
    retry_attempts: int = 3
    circuit_window: int = 20
    circuit_failure_ratio: float = 0.5
    circuit_open_seconds: float = 30.0
    half_open_probes: int = 2
    max_response_bytes: int = 5_242_880
    max_records_per_page: int = 1_000
    retention_batch_size: int = 500
    statement_timeout_ms: int = 5_000
    lease_seconds: int = 30
    pending_publication_max_seconds: int = 300

    def __post_init__(self) -> None:
        positive_fields = (
            "worker_pool_size",
            "api_pool_size",
            "claim_batch_size",
            "global_provider_concurrency",
            "per_provider_concurrency",
            "publication_concurrency",
            "retention_concurrency",
            "connect_timeout_seconds",
            "read_timeout_seconds",
            "total_timeout_seconds",
            "retry_attempts",
            "circuit_window",
            "circuit_open_seconds",
            "half_open_probes",
            "max_response_bytes",
            "max_records_per_page",
            "retention_batch_size",
            "statement_timeout_ms",
            "lease_seconds",
            "pending_publication_max_seconds",
        )
        for name in positive_fields:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.per_provider_concurrency > self.global_provider_concurrency:
            raise ValueError("per-provider concurrency cannot exceed the global limit")
        if self.total_timeout_seconds < max(
            self.connect_timeout_seconds, self.read_timeout_seconds
        ):
            raise ValueError("total timeout must cover connect and read timeout bounds")
        if not 0 < self.circuit_failure_ratio <= 1:
            raise ValueError("circuit_failure_ratio must be within (0, 1]")

    @classmethod
    def from_environment(cls) -> IngestionSettings:
        return cls(
            worker_pool_size=_positive_int("U04_WORKER_POOL_SIZE", 5),
            api_pool_size=_positive_int("U04_API_POOL_SIZE", 2),
            claim_batch_size=_positive_int("U04_CLAIM_BATCH_SIZE", 100),
            global_provider_concurrency=_positive_int("U04_PROVIDER_CONCURRENCY", 4),
            per_provider_concurrency=_positive_int("U04_PER_PROVIDER_CONCURRENCY", 1),
            publication_concurrency=_positive_int("U04_PUBLICATION_CONCURRENCY", 1),
            retention_concurrency=_positive_int("U04_RETENTION_CONCURRENCY", 1),
            connect_timeout_seconds=_positive_float("U04_CONNECT_TIMEOUT_SECONDS", 0.3),
            read_timeout_seconds=_positive_float("U04_READ_TIMEOUT_SECONDS", 4.0),
            total_timeout_seconds=_positive_float("U04_TOTAL_TIMEOUT_SECONDS", 5.0),
            retry_attempts=_positive_int("U04_RETRY_ATTEMPTS", 3),
            circuit_window=_positive_int("U04_CIRCUIT_WINDOW", 20),
            circuit_failure_ratio=_ratio("U04_CIRCUIT_FAILURE_RATIO", 0.5),
            circuit_open_seconds=_positive_float("U04_CIRCUIT_OPEN_SECONDS", 30.0),
            half_open_probes=_positive_int("U04_HALF_OPEN_PROBES", 2),
            max_response_bytes=_positive_int("U04_MAX_RESPONSE_BYTES", 5_242_880),
            max_records_per_page=_positive_int("U04_MAX_RECORDS_PER_PAGE", 1_000),
            retention_batch_size=_positive_int("U04_RETENTION_BATCH_SIZE", 500),
            statement_timeout_ms=_positive_int("U04_STATEMENT_TIMEOUT_MS", 5_000),
            lease_seconds=_positive_int("U04_LEASE_SECONDS", 30),
            pending_publication_max_seconds=_positive_int(
                "U04_PENDING_PUBLICATION_MAX_SECONDS", 300
            ),
        )
