from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ott_feed.engagement.config import EngagementSettings


def test_default_settings_match_approved_resource_budgets() -> None:
    settings = EngagementSettings()
    assert (
        settings.api_db_pool_size,
        settings.worker_db_pool_size,
        settings.maintenance_db_pool_size,
    ) == (4, 2, 1)
    assert (settings.in_app_concurrency, settings.email_concurrency) == (2, 2)
    assert (settings.email_timeout_seconds, settings.email_max_attempts) == (5, 3)


def test_settings_reject_non_positive_or_unbounded_concurrency() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        EngagementSettings(worker_db_pool_size=0)
    with pytest.raises(ValueError, match="cannot exceed claim size"):
        EngagementSettings(email_concurrency=51)


def test_domain_and_application_packages_have_no_framework_imports() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "engagement"
    prohibited = {"fastapi", "pydantic", "sqlalchemy", "psycopg", "httpx"}
    for package in (root / "domain", root / "application"):
        for source in package.glob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            imported = {
                node.names[0].name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
            }
            imported.update(
                node.module.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            )
            assert imported.isdisjoint(prohibited), source
