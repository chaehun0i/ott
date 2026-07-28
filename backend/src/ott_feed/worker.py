"""Worker bootstrap. Business units register typed handlers at composition time."""

from ott_feed.catalog.worker import CatalogWorkerHandlers, U03LaneBudgets, register_catalog_handlers
from ott_feed.identity.config import IdentitySettings
from ott_feed.identity.worker import IdentityWorkerHandlers, LaneBudgets, register_identity_handlers
from ott_feed.platform.application.outbox import HandlerRegistry
from ott_feed.platform.config import Settings
from ott_feed.search.worker import SearchWorkerHandlers, register_search_handlers


def build_worker_registry(
    settings: Settings | None = None,
    identity_handlers: IdentityWorkerHandlers | None = None,
    identity_settings: IdentitySettings | None = None,
    catalog_handlers: CatalogWorkerHandlers | None = None,
    search_handlers: SearchWorkerHandlers | None = None,
    u03_budgets: U03LaneBudgets | None = None,
) -> HandlerRegistry:
    platform_settings = settings or Settings.from_environment()
    registry = HandlerRegistry()
    if identity_handlers is not None:
        resolved_identity = identity_settings or IdentitySettings.from_environment(
            platform_settings.environment
        )
        register_identity_handlers(
            registry,
            identity_handlers,
            LaneBudgets(
                resolved_identity.worker_high_limit,
                resolved_identity.worker_normal_limit,
                resolved_identity.worker_low_limit,
            ),
        )
    if catalog_handlers is not None or search_handlers is not None:
        resolved_budgets = u03_budgets or U03LaneBudgets()
        if catalog_handlers is not None:
            register_catalog_handlers(registry, catalog_handlers, resolved_budgets)
        if search_handlers is not None:
            register_search_handlers(registry, search_handlers, resolved_budgets)
    return registry
