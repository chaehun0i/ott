from pathlib import Path


def test_telemetry_does_not_accept_raw_query_vector_or_provider_payload() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed"
    telemetry = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root / "catalog", root / "search")
        for path in path.rglob("telemetry.py")
    )
    assert "raw_query" not in telemetry
    assert "provider_payload" not in telemetry
    assert "embedding_vector" not in telemetry
