from dataclasses import replace

from fastapi.testclient import TestClient

from ott_feed.identity.config import IdentitySettings
from ott_feed.main import create_app
from ott_feed.platform.application.rate_limit import InMemoryRateLimiter, RatePolicy
from ott_feed.platform.config import Settings
from ott_feed.platform.health import HealthRegistry


def test_health_contract_and_correlation_header() -> None:
    health = HealthRegistry()
    health.add("database", lambda: True)
    app = create_app(
        Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"0123456789abcdef"), health
    )
    response = TestClient(app).get("/api/v1/health/ready", headers={"x-correlation-id": "corr-1"})
    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "corr-1"
    assert response.json() == {"status": "ready", "checks": {"database": "up"}}


def test_deep_health_requires_operator_and_openapi_is_versioned() -> None:
    app = create_app(
        Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"0123456789abcdef")
    )
    client = TestClient(app)
    assert client.get("/api/v1/health/deep").status_code == 403
    assert (
        client.get("/api/v1/health/deep", headers={"x-operator-role": "operator"}).status_code
        == 200
    )
    schema = client.get("/api/v1/openapi.json").json()
    assert schema["info"]["version"] == "1.0.0"


def test_remote_environment_disables_interactive_and_openapi_routes() -> None:
    app = create_app(
        Settings("remote", "postgresql+psycopg://db", "example.com", b"0123456789abcdef"),
        identity_settings=replace(IdentitySettings.from_environment("local"), environment="remote"),
    )
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/api/v1/openapi.json").status_code == 404


def test_api_rate_limit_returns_429_and_retry_after() -> None:
    policies = {
        name: RatePolicy(1, 0.01)
        for name in ("public", "authentication", "recommendation", "administration")
    }
    app = create_app(
        Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"0123456789abcdef"),
        rate_limiter=InMemoryRateLimiter(policies),
    )
    client = TestClient(app)
    assert client.get("/api/v1/health/live").status_code == 200
    limited = client.get("/api/v1/health/live")
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1


def test_metrics_contract_is_prometheus_text() -> None:
    app = create_app(
        Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"0123456789abcdef")
    )
    response = TestClient(app).get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "ott_platform_up 1" in response.text
