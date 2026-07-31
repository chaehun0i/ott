from fastapi.testclient import TestClient

from ott_feed.engagement.api.contracts import (
    IncidentView,
    NotificationView,
    OverrideRequest,
    TraceView,
)
from ott_feed.main import create_app
from ott_feed.platform.config import Settings


class FakeFacade:
    def notifications(self, member_ref: str, limit: int) -> list[NotificationView]:
        return [
            NotificationView(
                notification_id="n",
                content_id="c",
                event_type="new",
                channel="in_app",
                created_at="2026-07-31T00:00:00Z",
            )
        ]

    def override(self, content_id: str, request: OverrideRequest, actor_ref: str) -> str:
        return "operation-1"

    def trace(self, trace_id: str) -> TraceView | None:
        return TraceView(request_id="request-1", reason_codes=["genre_match"])

    def incidents(self, limit: int) -> list[IncidentView]:
        return [IncidentView(incident_id="i", severity="high", state="open", version=0)]


def client() -> TestClient:
    return TestClient(
        create_app(
            settings=Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"test-key"),
            engagement_facade=FakeFacade(),
        )
    )


def test_notification_and_privileged_contracts() -> None:
    response = client().get("/api/v1/engagement/notifications", headers={"x-member-ref": "m"})
    assert response.status_code == 200
    denied = client().get("/api/v1/engagement/admin/traces/secret")
    missing = client().get(
        "/api/v1/engagement/admin/traces/missing", headers={"x-operator-role": "viewer"}
    )
    assert (denied.status_code, denied.json()) == (missing.status_code, missing.json())
    allowed = client().get(
        "/api/v1/engagement/admin/traces/t", headers={"x-operator-role": "administrator"}
    )
    assert allowed.json()["request_id"] == "request-1"
