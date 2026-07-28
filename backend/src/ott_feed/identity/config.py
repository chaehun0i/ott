"""Fail-fast U02 configuration loaded from environment and secret files."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ott_feed.platform.config import read_secret


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    value = default if raw is None else int(raw)
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _required_secret(name: str, environment: str) -> bytes:
    value = read_secret(os.getenv(f"{name}_FILE")) or os.getenv(name)
    if value:
        return value.encode()
    if environment in {"local", "test"}:
        return f"{environment}-only-{name.lower()}-change-me".encode()
    raise ValueError(f"{name}_FILE is required outside local environment")


@dataclass(frozen=True, slots=True)
class IdentitySettings:
    environment: str
    argon2_memory_kib: int
    argon2_time_cost: int
    argon2_parallelism: int
    argon2_executor_limit: int
    session_inactivity_seconds: int
    session_absolute_seconds: int
    fresh_auth_seconds: int
    cookie_secure: bool
    cookie_samesite: str
    current_key_version: int
    kek: bytes
    blind_index_key: bytes
    session_pepper: bytes
    export_key: bytes
    google_client_id: str | None
    google_client_secret: str | None
    google_redirect_uri: str | None
    email_host: str | None
    email_port: int
    email_username: str | None
    email_password: str | None
    email_sender: str | None
    export_bucket: str | None
    api_pool_size: int
    worker_pool_size: int
    worker_high_limit: int
    worker_normal_limit: int
    worker_low_limit: int

    @classmethod
    def from_environment(cls, environment: str | None = None) -> IdentitySettings:
        resolved_environment: str = environment or os.getenv("APP_ENV") or "local"
        same_site = os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower()
        if same_site != "lax":
            raise ValueError("U02 requires SESSION_COOKIE_SAMESITE=lax")
        settings = cls(
            environment=resolved_environment,
            argon2_memory_kib=_positive_int("ARGON2_MEMORY_KIB", 65536),
            argon2_time_cost=_positive_int("ARGON2_TIME_COST", 3),
            argon2_parallelism=_positive_int("ARGON2_PARALLELISM", 1),
            argon2_executor_limit=_positive_int("ARGON2_EXECUTOR_LIMIT", 2),
            session_inactivity_seconds=_positive_int("SESSION_INACTIVITY_SECONDS", 1800),
            session_absolute_seconds=_positive_int("SESSION_ABSOLUTE_SECONDS", 2592000),
            fresh_auth_seconds=_positive_int("FRESH_AUTH_SECONDS", 600),
            cookie_secure=os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true",
            cookie_samesite=same_site,
            current_key_version=_positive_int("IDENTITY_KEY_VERSION", 1),
            kek=_required_secret("IDENTITY_KEK", resolved_environment),
            blind_index_key=_required_secret("IDENTITY_BLIND_INDEX_KEY", resolved_environment),
            session_pepper=_required_secret("IDENTITY_SESSION_PEPPER", resolved_environment),
            export_key=_required_secret("IDENTITY_EXPORT_KEY", resolved_environment),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
            google_client_secret=read_secret(os.getenv("GOOGLE_CLIENT_SECRET_FILE")),
            google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            email_host=os.getenv("EMAIL_HOST"),
            email_port=_positive_int("EMAIL_PORT", 1025),
            email_username=os.getenv("EMAIL_USERNAME"),
            email_password=read_secret(os.getenv("EMAIL_PASSWORD_FILE")),
            email_sender=os.getenv("EMAIL_SENDER"),
            export_bucket=os.getenv("IDENTITY_EXPORT_BUCKET"),
            api_pool_size=_positive_int("IDENTITY_API_POOL_SIZE", 10),
            worker_pool_size=_positive_int("IDENTITY_WORKER_POOL_SIZE", 5),
            worker_high_limit=_positive_int("IDENTITY_WORKER_HIGH_LIMIT", 2),
            worker_normal_limit=_positive_int("IDENTITY_WORKER_NORMAL_LIMIT", 2),
            worker_low_limit=_positive_int("IDENTITY_WORKER_LOW_LIMIT", 1),
        )
        if settings.argon2_memory_kib < 65536:
            raise ValueError("ARGON2_MEMORY_KIB must be at least 65536")
        if settings.environment != "local" and not settings.cookie_secure:
            raise ValueError("secure session cookies are required outside local environment")
        if settings.environment == "remote" and not all(
            (
                settings.google_client_id,
                settings.google_client_secret,
                settings.google_redirect_uri,
            )
        ):
            raise ValueError("remote Google OAuth configuration is incomplete")
        if settings.environment == "remote" and not all(
            (
                settings.email_host,
                settings.email_username,
                settings.email_password,
                settings.email_sender,
            )
        ):
            raise ValueError("remote email configuration is incomplete")
        if settings.environment == "remote" and not settings.export_bucket:
            raise ValueError("remote export storage configuration is required")
        return settings
