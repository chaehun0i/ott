from fastapi.testclient import TestClient

from ott_feed.main import create_app
from ott_feed.platform.config import Settings
from ott_feed.recommendation.api.contracts import RecommendationContract, RecommendationItemContract


class FakeFacade:
    def recommend(self, owner_id, request, idempotency_key):
        assert owner_id == "user-1" and idempotency_key == "key-1"
        return RecommendationContract(
            request_id="r1",
            intent_version="intent-v1",
            confirmation_required=False,
            degraded_reasons=[],
            items=[
                RecommendationItemContract(
                    content_id="a",
                    title="A",
                    summary="S",
                    reason="R",
                    score=1.0,
                    metadata_version="m1",
                )
            ],
        )

    refine = recommend

    def reset(self, owner_id, session_id, request, idempotency_key):
        assert owner_id == "user-1" and session_id == "s1" and request.expected_version == 1


def client() -> TestClient:
    settings = Settings("test", "postgresql+psycopg://db", "localhost", b"0123456789abcdef")
    return TestClient(create_app(settings=settings, recommendation_facade=FakeFacade()))


def test_recommendation_contract_and_openapi() -> None:
    response = client().post(
        "/api/v1/recommendations",
        headers={"x-user-id": "user-1", "idempotency-key": "key-1"},
        json={"text": "comedy", "locale": "en-US"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["content_id"] == "a"
    schema = client().get("/api/v1/openapi.json").json()
    assert "/api/v1/recommendations" in schema["paths"]


def test_authentication_error_is_non_enumerating() -> None:
    response = client().post(
        "/api/v1/recommendations",
        headers={"idempotency-key": "key"},
        json={"text": "comedy", "locale": "en-US"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "authentication_required"


def test_reset_contract() -> None:
    response = client().post(
        "/api/v1/recommendations/s1/reset",
        headers={"x-user-id": "user-1", "idempotency-key": "key"},
        json={"expected_version": 1},
    )
    assert response.status_code == 204
