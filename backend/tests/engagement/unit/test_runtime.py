from ott_feed.engagement.maintenance import run
from ott_feed.engagement.worker import EngagementWorkerHandlers, register_engagement_handlers
from ott_feed.platform.application.outbox import HandlerRegistry


def test_worker_registers_isolated_channel_concurrency() -> None:
    registry = HandlerRegistry()
    handlers = EngagementWorkerHandlers(lambda payload: None, lambda payload: None)
    register_engagement_handlers(registry, handlers)
    assert registry.job_types == ("u06.notification.in_app", "u06.notification.email")


def test_maintenance_rejects_unknown_command() -> None:
    assert run("verify-audit") == 0
    assert run("unknown") == 64
