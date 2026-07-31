"""Validated U06 runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class EngagementSettings:
    api_db_pool_size: int = 4
    worker_db_pool_size: int = 2
    maintenance_db_pool_size: int = 1
    in_app_concurrency: int = 2
    email_concurrency: int = 2
    maintenance_concurrency: int = 1
    in_app_claim_size: int = 100
    email_claim_size: int = 50
    maintenance_claim_size: int = 500
    email_timeout_seconds: int = 5
    email_max_attempts: int = 3

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.in_app_concurrency > self.in_app_claim_size:
            raise ValueError("in-app concurrency cannot exceed claim size")
        if self.email_concurrency > self.email_claim_size:
            raise ValueError("email concurrency cannot exceed claim size")

    @classmethod
    def from_environment(cls) -> EngagementSettings:
        return cls(
            api_db_pool_size=_positive_int("U06_API_DB_POOL_SIZE", 4),
            worker_db_pool_size=_positive_int("U06_WORKER_DB_POOL_SIZE", 2),
            maintenance_db_pool_size=_positive_int("U06_MAINTENANCE_DB_POOL_SIZE", 1),
            in_app_concurrency=_positive_int("U06_IN_APP_CONCURRENCY", 2),
            email_concurrency=_positive_int("U06_EMAIL_CONCURRENCY", 2),
            maintenance_concurrency=_positive_int("U06_MAINTENANCE_CONCURRENCY", 1),
            in_app_claim_size=_positive_int("U06_IN_APP_CLAIM_SIZE", 100),
            email_claim_size=_positive_int("U06_EMAIL_CLAIM_SIZE", 50),
            maintenance_claim_size=_positive_int("U06_MAINTENANCE_CLAIM_SIZE", 500),
            email_timeout_seconds=_positive_int("U06_EMAIL_TIMEOUT_SECONDS", 5),
            email_max_attempts=_positive_int("U06_EMAIL_MAX_ATTEMPTS", 3),
        )
