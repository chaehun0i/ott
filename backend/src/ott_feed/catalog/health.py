"""Catalog readiness and deep-health contributions."""

from dataclasses import dataclass

from ott_feed.platform.health import HealthCheck, HealthRegistry


@dataclass(frozen=True, slots=True)
class CatalogHealthContributor:
    database_extensions: HealthCheck
    active_feed_generation: HealthCheck
    projection_gap_free: HealthCheck

    def register(self, registry: HealthRegistry) -> None:
        registry.add("catalog_database_extensions", self.database_extensions, required=True)
        registry.add("catalog_active_feed_generation", self.active_feed_generation, required=True)
        registry.add("catalog_projection_gap_free", self.projection_gap_free, required=False)
