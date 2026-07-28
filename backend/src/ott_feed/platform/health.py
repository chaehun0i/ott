"""Low-cost liveness and composable readiness/deep health checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

HealthCheck = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class HealthResult:
    status: str
    checks: dict[str, str]


class HealthRegistry:
    def __init__(self) -> None:
        self.required: dict[str, HealthCheck] = {}
        self.optional: dict[str, HealthCheck] = {}

    def add(self, name: str, check: HealthCheck, *, required: bool = True) -> None:
        (self.required if required else self.optional)[name] = check

    def readiness(self) -> HealthResult:
        checks = {name: "up" if check() else "down" for name, check in self.required.items()}
        return HealthResult(
            "ready" if all(value == "up" for value in checks.values()) else "not_ready", checks
        )

    def deep(self) -> HealthResult:
        checks = {
            name: "up" if check() else "down"
            for name, check in {**self.required, **self.optional}.items()
        }
        return HealthResult(
            "healthy" if all(value == "up" for value in checks.values()) else "degraded", checks
        )


@dataclass(frozen=True, slots=True)
class IdentityHealthContributor:
    database: HealthCheck
    worker_backlog_ok: HealthCheck
    google_circuit_ok: HealthCheck
    argon2_capacity_ok: HealthCheck

    def register(self, registry: HealthRegistry) -> None:
        registry.add("identity_database", self.database, required=True)
        registry.add("identity_worker_backlog", self.worker_backlog_ok, required=True)
        registry.add("identity_google_circuit", self.google_circuit_ok, required=False)
        registry.add("identity_argon2_capacity", self.argon2_capacity_ok, required=False)
