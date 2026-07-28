import ast
from pathlib import Path


def test_u07_has_no_business_unit_implementation_imports() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "platform"
    forbidden = (
        "ott_feed.identity",
        "ott_feed.catalog",
        "ott_feed.ingestion",
        "ott_feed.recommendation",
        "ott_feed.engagement",
    )
    sources = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
    assert not any(name in sources for name in forbidden)


def test_u02_core_does_not_import_framework_or_adapter_packages() -> None:
    identity_root = Path(__file__).parents[3] / "src" / "ott_feed" / "identity"
    core_directories = (identity_root / "domain", identity_root / "application")
    forbidden = {"fastapi", "sqlalchemy", "authlib", "argon2", "cryptography"}
    imported_roots: set[str] = set()
    for directory in core_directories:
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(forbidden)


def test_u03_core_does_not_import_framework_or_adapter_packages() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed"
    core_directories = (
        root / "catalog" / "domain",
        root / "catalog" / "application",
        root / "search" / "domain",
        root / "search" / "application",
    )
    forbidden = {"fastapi", "sqlalchemy", "httpx", "pgvector"}
    imported_roots: set[str] = set()
    for directory in core_directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(forbidden)


def test_u04_core_does_not_import_framework_or_adapter_packages() -> None:
    root = Path(__file__).parents[3] / "src" / "ott_feed" / "ingestion"
    core_directories = (root / "domain", root / "application")
    forbidden = {"fastapi", "sqlalchemy", "httpx", "psycopg"}
    imported_roots: set[str] = set()
    for directory in core_directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(forbidden)
