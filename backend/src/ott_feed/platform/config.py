"""Validated environment configuration and file-based secret loading."""

import os
from dataclasses import dataclass
from pathlib import Path


def read_secret(path: str | None) -> str | None:
    if not path:
        return None
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"secret file is empty: {path}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    database_url: str
    domain: str
    cursor_secret: bytes

    @classmethod
    def from_environment(cls) -> "Settings":
        environment = os.getenv("APP_ENV", "local")
        database_secret = read_secret(os.getenv("DATABASE_URL_FILE"))
        database_url = (
            database_secret
            if database_secret is not None
            else os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:")
        )
        domain = os.getenv("APP_DOMAIN", "localhost")
        secret = read_secret(os.getenv("API_SECRET_FILE")) or os.getenv(
            "API_SECRET", "local-only-secret-change-me"
        )
        if secret is None:
            raise ValueError("API secret is required")
        if environment == "remote" and secret == "local-only-secret-change-me":
            raise ValueError("remote environment requires API_SECRET_FILE")
        return cls(environment, database_url, domain, secret.encode())
