"""Layered U04 health contribution."""

from __future__ import annotations

from collections.abc import Callable

from ott_feed.platform.health import HealthRegistry


class IngestionHealthContributor:
    def __init__(
        self,
        database_ready: Callable[[], bool],
        rule_ready: Callable[[], bool],
        publication_ready: Callable[[], bool],
        provider_degraded: Callable[[], bool] = lambda: False,
    ) -> None:
        self.database_ready = database_ready
        self.rule_ready = rule_ready
        self.publication_ready = publication_ready
        self.provider_degraded = provider_degraded

    def register(self, registry: HealthRegistry) -> None:
        registry.add("u04_database", self.database_ready, required=True)
        registry.add("u04_validation_rules", self.rule_ready, required=True)
        registry.add("u04_publication", self.publication_ready, required=False)
        registry.add("u04_provider_degraded", lambda: not self.provider_degraded(), required=False)
