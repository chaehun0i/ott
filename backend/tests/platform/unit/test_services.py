import json
import logging
from datetime import UTC, datetime, timedelta

import pytest

from ott_feed.platform.application.outbox import HandlerRegistry, WorkerDispatcher
from ott_feed.platform.application.rate_limit import InMemoryRateLimiter, RatePolicy
from ott_feed.platform.application.resilience import (
    BulkheadRegistry,
    CircuitState,
    DependencyPolicy,
    ResilientExecutor,
)
from ott_feed.platform.config import Settings, read_secret
from ott_feed.platform.domain.errors import PlatformError
from ott_feed.platform.domain.models import JobStatus, OutboxJob
from ott_feed.platform.telemetry import JsonFormatter, Metrics, NonBlockingTelemetryBuffer


def test_rate_limiter_returns_retry_contract() -> None:
    limiter = InMemoryRateLimiter({"public": RatePolicy(1, 0.01)})
    limiter.consume("public", "ip-1")
    with pytest.raises(PlatformError) as captured:
        limiter.consume("public", "ip-1")
    assert captured.value.status_code == 429
    assert captured.value.safe_details and captured.value.safe_details["retryAfterSeconds"] >= 1


class MemoryOutbox:
    def __init__(self, job: OutboxJob) -> None:
        self.job = job

    def claim(
        self, worker_id: str, job_types: tuple[str, ...], lease_for: timedelta
    ) -> OutboxJob | None:
        if self.job.job_type not in job_types or self.job.status not in {
            JobStatus.PENDING,
            JobStatus.RETRY_WAIT,
        }:
            return None
        self.job.claim(worker_id, lease_for)
        return self.job

    def save(self, job: OutboxJob) -> None:
        self.job = job


def test_worker_dispatcher_success_failure_and_registry_guards() -> None:
    success = OutboxJob("success", {})
    success_repo = MemoryOutbox(success)
    registry = HandlerRegistry()
    registry.register("success", lambda payload: None)
    with pytest.raises(ValueError):
        registry.register("success", lambda payload: None)
    assert WorkerDispatcher("w1", success_repo, registry).run_once()
    assert success.status == JobStatus.SUCCEEDED
    assert not WorkerDispatcher("w1", success_repo, registry).run_once()

    failed = OutboxJob("failure", {}, max_attempts=1)
    failed_repo = MemoryOutbox(failed)
    failed_registry = HandlerRegistry()

    def fail(_: dict[str, object]) -> None:
        raise OSError("provider unavailable")

    failed_registry.register("failure", fail)
    assert WorkerDispatcher("w2", failed_repo, failed_registry).run_once()
    assert failed.status == JobStatus.DEAD_LETTER


@pytest.mark.anyio
async def test_resilient_executor_success_fallback_and_open_circuit() -> None:
    executor = ResilientExecutor(BulkheadRegistry({"provider": 1}))
    deadline = datetime.now(UTC) + timedelta(seconds=2)
    policy = DependencyPolicy(
        "provider",
        0.2,
        max_attempts=2,
        retry_safe=True,
        base_backoff_seconds=0,
        failure_threshold=1,
    )

    async def success() -> str:
        return "ok"

    assert await executor.execute(policy, "provider", success, deadline) == "ok"
    assert executor.circuits["provider"].state == CircuitState.CLOSED

    async def failure() -> str:
        raise OSError("down")

    async def fallback() -> str:
        return "degraded"

    assert await executor.execute(policy, "provider", failure, deadline, fallback) == "degraded"
    assert executor.circuits["provider"].state == CircuitState.OPEN
    assert await executor.execute(policy, "provider", failure, deadline, fallback) == "degraded"


@pytest.mark.anyio
async def test_resilient_executor_without_fallback_raises_safe_error() -> None:
    executor = ResilientExecutor(BulkheadRegistry({"provider": 1}))
    policy = DependencyPolicy("provider", 0.01)

    async def failure() -> str:
        raise OSError("raw internal address")

    with pytest.raises(PlatformError, match="unavailable"):
        await executor.execute(
            policy, "provider", failure, datetime.now(UTC) + timedelta(seconds=1)
        )


def test_telemetry_json_metrics_and_bounded_buffer() -> None:
    record = logging.LogRecord("ott", logging.INFO, __file__, 1, "handled", (), None)
    record.fields = {"token": "raw", "correlationId": "c1"}
    output = json.loads(JsonFormatter().format(record))
    assert output["token"] == "[REDACTED]"

    metrics = Metrics()
    metrics.increment("request", route="health")
    assert list(metrics.snapshot().values()) == [1]

    buffer = NonBlockingTelemetryBuffer(capacity=1)
    buffer.emit({"secret": "raw"})
    buffer.emit({"safe": "ok"})
    assert buffer.dropped == 1
    assert buffer.drain() == [{"safe": "ok"}]
    assert buffer.drain() == []


def test_settings_load_file_secret_and_reject_remote_default(tmp_path, monkeypatch) -> None:
    secret_file = tmp_path / "secret"
    database_file = tmp_path / "database-url"
    secret_file.write_text("0123456789abcdef", encoding="utf-8")
    database_file.write_text("postgresql+psycopg://u04_api@db/ott_feed", encoding="utf-8")
    assert read_secret(str(secret_file)) == "0123456789abcdef"
    monkeypatch.setenv("API_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("DATABASE_URL_FILE", str(database_file))
    monkeypatch.setenv("APP_ENV", "remote")
    settings = Settings.from_environment()
    assert settings.cursor_secret == b"0123456789abcdef"
    assert settings.database_url == "postgresql+psycopg://u04_api@db/ott_feed"

    monkeypatch.delenv("API_SECRET_FILE")
    monkeypatch.delenv("API_SECRET", raising=False)
    with pytest.raises(ValueError, match="requires API_SECRET_FILE"):
        Settings.from_environment()
