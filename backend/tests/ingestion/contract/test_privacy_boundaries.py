from pathlib import Path


def test_api_health_and_telemetry_never_reference_sensitive_provider_fields() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "ingestion"
    paths = (root / "api", root / "health.py", root / "telemetry.py")
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for target in paths
        for path in ((target,) if target.is_file() else tuple(target.rglob("*.py")))
    )
    for forbidden in ("payload_body", "provider_token", "url_query", "response_text"):
        assert forbidden not in sources


def test_u04_roles_have_no_direct_u03_grant() -> None:
    root = Path(__file__).parents[3]
    grants = (root / "migrations" / "role-grants.sql").read_text(encoding="utf-8").lower()
    assert "grant" in grants and "u04_worker_runtime" in grants
    for line in grants.splitlines():
        if "u03_catalog" in line and line.lstrip().startswith("grant"):
            assert "u04_" not in line


def test_u04_application_has_no_concrete_u03_persistence_import() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "ingestion" / "application"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
    assert "ott_feed.catalog.adapters" not in sources
