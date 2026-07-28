"""FastAPI application factory for platform, identity and approved discovery APIs."""

import hashlib

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from ott_feed.api.middleware import RateLimitMiddleware, RequestContextMiddleware, current_request
from ott_feed.api.openapi import docs_paths
from ott_feed.catalog.api.router import (
    CatalogFacade,
    UnavailableCatalogFacade,
    create_catalog_router,
)
from ott_feed.catalog.domain.errors import CatalogError
from ott_feed.catalog.health import CatalogHealthContributor
from ott_feed.identity.adapters.security import CsrfProtector
from ott_feed.identity.api.dependencies import IdentityFacade, UnavailableIdentityFacade
from ott_feed.identity.api.messages import localize
from ott_feed.identity.api.router import create_identity_router
from ott_feed.identity.config import IdentitySettings
from ott_feed.identity.domain.errors import IdentityError
from ott_feed.ingestion.api.router import (
    IngestionFacade,
    UnavailableIngestionFacade,
    create_ingestion_router,
)
from ott_feed.ingestion.domain.errors import IngestionError
from ott_feed.ingestion.health import IngestionHealthContributor
from ott_feed.platform.application.rate_limit import InMemoryRateLimiter, RatePolicy
from ott_feed.platform.config import Settings
from ott_feed.platform.health import HealthRegistry
from ott_feed.search.adapters.security import CursorSigner
from ott_feed.search.api.dependencies import SearchRateLimitAdapter
from ott_feed.search.api.router import SearchFacade, UnavailableSearchFacade, create_search_router
from ott_feed.search.domain.errors import SearchError
from ott_feed.search.health import SearchHealthContributor


def require_operator(x_operator_role: str | None = Header(default=None)) -> None:
    if x_operator_role != "operator":
        raise HTTPException(status_code=403, detail="operator access required")


def create_app(
    settings: Settings | None = None,
    health: HealthRegistry | None = None,
    rate_limiter: InMemoryRateLimiter | None = None,
    identity_facade: IdentityFacade | None = None,
    identity_settings: IdentitySettings | None = None,
    catalog_facade: CatalogFacade | None = None,
    search_facade: SearchFacade | None = None,
    cursor_signer: CursorSigner | None = None,
    catalog_health: CatalogHealthContributor | None = None,
    search_health: SearchHealthContributor | None = None,
    ingestion_facade: IngestionFacade | None = None,
    ingestion_health: IngestionHealthContributor | None = None,
) -> FastAPI:
    settings = settings or Settings.from_environment()
    health = health or HealthRegistry()
    identity_settings = identity_settings or IdentitySettings.from_environment(settings.environment)
    if catalog_health is not None:
        catalog_health.register(health)
    if search_health is not None:
        search_health.register(health)
    if ingestion_health is not None:
        ingestion_health.register(health)
    docs_url, redoc_url = docs_paths(settings.environment)
    app = FastAPI(
        title="OTT Feed API",
        version="1.0.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url="/api/v1/openapi.json" if docs_url else None,
    )
    resolved_rate_limiter = rate_limiter or InMemoryRateLimiter(
        {
            "public": RatePolicy(60, 1),
            "authentication": RatePolicy(10, 0.1),
            "recommendation": RatePolicy(12, 0.2),
            "administration": RatePolicy(20, 0.2),
            "semantic_anonymous": RatePolicy(9, 0.1),
            "semantic_authenticated": RatePolicy(30, 0.5),
        }
    )
    app.add_middleware(RateLimitMiddleware, limiter=resolved_rate_limiter)
    app.add_middleware(RequestContextMiddleware, timeout_seconds=15.0)
    app.state.identity_facade = identity_facade or UnavailableIdentityFacade()
    router = APIRouter(prefix="/api/v1")

    @app.exception_handler(IdentityError)
    async def identity_error_handler(request: Request, exc: IdentityError) -> JSONResponse:
        forbidden_codes = {
            "access_denied",
            "csrf_origin_invalid",
            "csrf_token_invalid",
            "oauth_claim_invalid",
        }
        unauthorized_codes = {"authentication_failed", "session_invalid", "session_missing"}
        status_code = (
            503
            if exc.retryable
            else 401
            if exc.code in unauthorized_codes
            else 403
            if exc.code in forbidden_codes
            else 409
            if "conflict" in exc.code or exc.code.endswith("_exists")
            else 400
        )
        context = current_request.get()
        correlation_id = context.correlation_id if context else "unavailable"
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": localize(exc.message_key, request.headers.get("accept-language")),
                    "messageKey": exc.message_key,
                    "correlationId": correlation_id,
                    "retryable": exc.retryable,
                }
            },
        )

    @app.exception_handler(CatalogError)
    @app.exception_handler(SearchError)
    @app.exception_handler(IngestionError)
    async def discovery_error_handler(
        request: Request, exc: CatalogError | SearchError | IngestionError
    ) -> JSONResponse:
        context = current_request.get()
        return JSONResponse(
            status_code=503 if exc.retryable else 400,
            content={
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "correlationId": context.correlation_id if context else "unavailable",
                    "retryable": exc.retryable,
                }
            },
        )

    @router.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @router.get("/health/ready", tags=["health"])
    def ready() -> dict[str, object]:
        result = health.readiness()
        if result.status != "ready":
            raise HTTPException(status_code=503, detail="service not ready")
        return {"status": result.status, "checks": result.checks}

    @router.get("/health/deep", tags=["health"], dependencies=[Depends(require_operator)])
    def deep() -> dict[str, object]:
        result = health.deep()
        return {"status": result.status, "checks": result.checks}

    @router.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(
            "# HELP ott_platform_up Platform process availability.\n"
            "# TYPE ott_platform_up gauge\n"
            "ott_platform_up 1\n",
            media_type="text/plain; version=0.0.4",
        )

    app.include_router(router)
    origins = {f"https://{settings.domain}"}
    if settings.environment in {"local", "test"}:
        origins.add(f"http://{settings.domain}")
    app.include_router(
        create_identity_router(
            CsrfProtector(settings.cursor_secret, frozenset(origins)),
            secure_cookies=identity_settings.cookie_secure,
        )
    )
    resolved_signer = cursor_signer or CursorSigner(
        hashlib.sha256(settings.cursor_secret + b":u03:cursor").digest()
    )
    app.include_router(
        create_catalog_router(catalog_facade or UnavailableCatalogFacade(), resolved_signer)
    )
    app.include_router(
        create_search_router(
            search_facade or UnavailableSearchFacade(),
            SearchRateLimitAdapter(resolved_rate_limiter),
        )
    )
    app.include_router(
        create_ingestion_router(ingestion_facade or UnavailableIngestionFacade(), require_operator)
    )
    return app


app = create_app()
