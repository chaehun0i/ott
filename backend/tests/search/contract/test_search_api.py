from fastapi.testclient import TestClient

from ott_feed.main import create_app
from ott_feed.platform.config import Settings
from ott_feed.search.api.contracts import SearchRequest
from ott_feed.search.domain.models import RankedResult, SearchCandidate


class SearchFacade:
    def search(self, request: SearchRequest) -> tuple[list[RankedResult], str | None, str]:
        candidate = SearchCandidate("c1", 1.0, "Funny", request.locale, "text")
        return [RankedResult(candidate, 1, ("text",))], "semantic_unavailable", "g1"


def test_search_contract_degraded_reason_and_privacy() -> None:
    app = create_app(
        Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"secret"),
        search_facade=SearchFacade(),
    )
    response = TestClient(app).post(
        "/api/v1/search", json={"query": "1시간 코미디", "region": "KR", "locale": "ko-KR"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["degradedReason"] == "semantic_unavailable"
    assert "query" not in body and response.headers["cache-control"] == "no-store"
