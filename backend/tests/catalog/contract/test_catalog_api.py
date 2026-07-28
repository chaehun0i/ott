from __future__ import annotations

from fastapi.testclient import TestClient

from ott_feed.catalog.application.detail import ContentDetail
from ott_feed.catalog.application.feed import FeedItem, FeedPage
from ott_feed.catalog.domain.models import FeedCursor
from ott_feed.main import create_app
from ott_feed.platform.config import Settings
from ott_feed.search.adapters.security import CursorSigner


class CatalogFacade:
    def feed(self, *, region: str, locale: str, page_size: int, cursor: str | None) -> FeedPage:
        item = FeedItem(
            "c1", "new", "제목", locale, "ko-KR", "netflix", "https://watch", "fresh", 1, 0.9
        )
        return FeedPage((item,), FeedCursor("fp", "g1", 0.9, "c1"), "g1", "fp")

    def detail(self, content_id: str, *, region: str, locale: str) -> ContentDetail:
        return ContentDetail(
            content_id,
            "제목",
            "요약",
            locale,
            "ko-KR",
            ("netflix",),
            ("https://watch",),
            "source",
            "r1",
            "fresh",
            1,
        )


def client() -> TestClient:
    return TestClient(
        create_app(
            Settings("test", "sqlite+pysqlite:///:memory:", "localhost", b"secret"),
            catalog_facade=CatalogFacade(),
            cursor_signer=CursorSigner(b"x" * 32),
        )
    )


def test_feed_detail_and_openapi_contract() -> None:
    response = client().get("/api/v1/feed", params={"region": "KR", "locale": "ko-KR"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["items"][0]["actual_locale"] == "ko-KR"
    detail = client().get("/api/v1/contents/c1", params={"region": "KR"})
    assert detail.status_code == 200 and detail.json()["sourceProvider"] == "source"
    schema = client().get("/api/v1/openapi.json").json()
    assert "/api/v1/feed" in schema["paths"] and "/api/v1/search" in schema["paths"]


def test_region_and_page_limits_are_rejected() -> None:
    assert client().get("/api/v1/feed").status_code == 422
    assert client().get("/api/v1/feed", params={"region": "KR", "pageSize": 51}).status_code == 422
