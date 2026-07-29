"""Layered U05 health contribution."""

from collections.abc import Callable

from ott_feed.platform.health import HealthRegistry


class RecommendationHealthContributor:
    def __init__(
        self,
        database_ready: Callable[[], bool],
        catalog_ready: Callable[[], bool],
        rules_ready: Callable[[], bool],
        feature_ready: Callable[[], bool] = lambda: True,
        ai_ready: Callable[[], bool] = lambda: True,
    ) -> None:
        self.database_ready = database_ready
        self.catalog_ready = catalog_ready
        self.rules_ready = rules_ready
        self.feature_ready = feature_ready
        self.ai_ready = ai_ready

    def register(self, registry: HealthRegistry) -> None:
        registry.add("u05_database", self.database_ready, required=True)
        registry.add("u05_catalog", self.catalog_ready, required=True)
        registry.add("u05_validation_rules", self.rules_ready, required=True)
        registry.add("u05_features", self.feature_ready, required=False)
        registry.add("u05_ai", self.ai_ready, required=False)
