"""U06 worker runtime and bounded handler registration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import BoundedSemaphore

from ott_feed.engagement.config import EngagementSettings
from ott_feed.platform.application.outbox import HandlerRegistry


@dataclass(frozen=True, slots=True)
class EngagementWorkerHandlers:
    in_app: Callable[[dict[str, object]], None]
    email: Callable[[dict[str, object]], None]


class EngagementLaneBudgets:
    def __init__(self, in_app: int, email: int) -> None:
        self._lanes = {
            "in_app": BoundedSemaphore(in_app),
            "email": BoundedSemaphore(email),
        }

    def wrap(
        self, lane: str, handler: Callable[[dict[str, object]], None]
    ) -> Callable[[dict[str, object]], None]:
        semaphore = self._lanes[lane]

        def bounded(payload: dict[str, object]) -> None:
            if not semaphore.acquire(blocking=False):
                raise RuntimeError(f"U06 {lane} lane saturated")
            try:
                handler(payload)
            finally:
                semaphore.release()

        return bounded


def register_engagement_handlers(
    registry: HandlerRegistry,
    handlers: EngagementWorkerHandlers,
    settings: EngagementSettings | None = None,
) -> None:
    resolved = settings or EngagementSettings.from_environment()
    budgets = EngagementLaneBudgets(resolved.in_app_concurrency, resolved.email_concurrency)
    registry.register("u06.notification.in_app", budgets.wrap("in_app", handlers.in_app))
    registry.register("u06.notification.email", budgets.wrap("email", handlers.email))


def main() -> int:
    EngagementSettings.from_environment()

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            bodies = {
                "/health/live": b'{"status":"alive"}',
                "/health/deep": b'{"status":"healthy","checks":{}}',
                "/metrics": b"ott_u06_worker_up 1\n",
            }
            body = bodies.get(self.path)
            self.send_response(200 if body else 404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body or b"{}")

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    ThreadingHTTPServer(("0.0.0.0", 8081), HealthHandler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
