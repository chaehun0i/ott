from collections.abc import Mapping

from fastapi.testclient import TestClient

from ott_feed.main import create_app
from ott_feed.platform.config import Settings


class Facade:
    def current_rule_contract(self) -> Mapping[str, object]:
        return {
            "contract_version": "u05-validation-v1",
            "rule_version": "rules-v1",
            "required_evidence_fields": ["title"],
            "allowed_content_types": ["movie", "series"],
            "max_runtime_minutes": 360,
        }

    def job_status(self, job_id: str) -> Mapping[str, object]:
        return {
            "job_id": job_id,
            "provider_id": "provider-1",
            "status": "running",
            "durable_cursor_present": True,
            "succeeded_count": 2,
            "quarantined_count": 1,
            "failed_count": 0,
        }

    def retry_quarantine(
        self, quarantine_id: str, target_rule_version: str, actor_reference: str
    ) -> str:
        return f"{quarantine_id}:{target_rule_version}:{actor_reference}"


def client() -> TestClient:
    return TestClient(
        create_app(
            settings=Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"secret"),
            ingestion_facade=Facade(),
        )
    )


def test_rule_contract_is_versioned_and_public() -> None:
    response = client().get("/api/v1/ingestion/rules/current")
    assert response.status_code == 200
    assert response.json()["rule_version"] == "rules-v1"


def test_operator_status_and_retry_require_role() -> None:
    value = client()
    assert value.get("/api/v1/ingestion/jobs/job-1").status_code == 403
    status = value.get("/api/v1/ingestion/jobs/job-1", headers={"x-operator-role": "operator"})
    assert status.status_code == 200
    retry = value.post(
        "/api/v1/ingestion/quarantine/q-1/retry",
        headers={"x-operator-role": "operator", "x-actor-reference": "operator:pseudo"},
        json={"target_rule_version": "rules-v2"},
    )
    assert retry.status_code == 200
    assert retry.json()["status"] == "scheduled"


def test_openapi_contains_u04_contracts_without_internal_payload_fields() -> None:
    schema = client().get("/api/v1/openapi.json").json()
    serialized = str(schema)
    assert "/api/v1/ingestion/rules/current" in schema["paths"]
    assert "payload_body" not in serialized
    assert "provider_token" not in serialized
