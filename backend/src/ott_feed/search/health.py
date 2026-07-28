"""Search readiness with separately degraded embedding capability."""

from dataclasses import dataclass

from ott_feed.platform.health import HealthCheck, HealthRegistry


@dataclass(frozen=True, slots=True)
class SearchHealthContributor:
    active_search_generation: HealthCheck
    embedding_available: HealthCheck
    rebuild_capacity_ok: HealthCheck

    def register(self, registry: HealthRegistry) -> None:
        registry.add("search_active_generation", self.active_search_generation, required=True)
        registry.add("search_embedding", self.embedding_available, required=False)
        registry.add("search_rebuild_capacity", self.rebuild_capacity_ok, required=False)
