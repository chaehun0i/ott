"""Correlation, deadline and safe error middleware."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import monotonic
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from ott_feed.platform.application.rate_limit import InMemoryRateLimiter
from ott_feed.platform.domain.errors import PlatformError


@dataclass(frozen=True, slots=True)
class RequestContext:
    correlation_id: str
    deadline: datetime
    identity: str | None
    locale: str
    api_version: int
    trace_id: str | None


current_request: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, limiter: InMemoryRateLimiter) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        bucket_class = (
            "administration"
            if "/admin" in path or "/health/deep" in path
            else "authentication"
            if "/auth" in path
            else "recommendation"
            if "/recommend" in path
            else "public"
        )
        identity = request.headers.get("x-authenticated-subject")
        client_ip = request.client.host if request.client else "unknown"
        self.limiter.consume(bucket_class, identity or client_ip)
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, timeout_seconds: float = 15.0) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = monotonic()
        correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
        identity = request.headers.get("x-authenticated-subject")
        locale = request.headers.get("accept-language", "ko").split(",", maxsplit=1)[0]
        context = RequestContext(
            correlation_id=correlation_id,
            deadline=datetime.now(UTC) + timedelta(seconds=self.timeout_seconds),
            identity=identity,
            locale=locale,
            api_version=1,
            trace_id=(request.headers.get("traceparent") or "").split("-")[1]
            if (request.headers.get("traceparent") or "").count("-") >= 3
            else None,
        )
        token = current_request.set(context)
        try:
            response = await call_next(request)
        except PlatformError as exc:
            headers: dict[str, str] = {}
            if exc.status_code == 429 and exc.safe_details:
                retry_after = exc.safe_details.get("retryAfterSeconds")
                if isinstance(retry_after, int):
                    headers["Retry-After"] = str(retry_after)
            response = JSONResponse(
                status_code=exc.status_code,
                headers=headers,
                content={
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "correlationId": correlation_id,
                        "retryable": exc.retryable,
                        "details": exc.safe_details,
                    }
                },
            )
        except Exception:
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "Unexpected server error",
                        "correlationId": correlation_id,
                        "retryable": False,
                    }
                },
            )
        finally:
            current_request.reset(token)
        response.headers["x-correlation-id"] = correlation_id
        response.headers["server-timing"] = f"app;dur={(monotonic() - started) * 1000:.2f}"
        return response
