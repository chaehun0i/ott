from fastapi.testclient import TestClient

from ott_feed.main import create_app


def test_browser_telemetry_accepts_bounded_allowlisted_events() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/telemetry/browser",
        json=[{"name": "web_vital", "route": "/feed", "outcome": "ok", "value": 12.0}],
    )
    assert response.status_code == 204


def test_browser_telemetry_rejects_sensitive_or_unknown_fields() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/telemetry/browser",
        json=[{"name": "ui_error", "route": "/feed", "outcome": "fail", "prompt": "secret"}],
    )
    assert response.status_code == 422
