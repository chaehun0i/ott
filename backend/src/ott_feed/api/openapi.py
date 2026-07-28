"""OpenAPI exposure policy and deterministic artifact export."""

import json
from pathlib import Path

from fastapi import FastAPI


def docs_paths(environment: str) -> tuple[str | None, str | None]:
    if environment in {"local", "test"}:
        return "/docs", "/redoc"
    return None, None


def export_openapi(app: FastAPI, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
