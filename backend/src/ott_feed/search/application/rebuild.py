"""Online immutable rebuild with quality gate and atomic active-pointer swap."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from ott_feed.search.application.quality import QualityResult
from ott_feed.search.ports import SearchTelemetryPort


@dataclass(frozen=True, slots=True)
class RebuildResult:
    generation_id: str
    previous_generation_id: str | None
    activated: bool
    reason: str | None = None


class OnlineRebuildService:
    def __init__(
        self,
        *,
        active: Callable[[str], str | None],
        compare_and_swap: Callable[[str, str | None, str], bool],
        build: Callable[[str], None],
        validate: Callable[[str], QualityResult],
        telemetry: SearchTelemetryPort,
        recall_threshold: float = 0.85,
        ndcg_threshold: float = 0.80,
        latency_threshold_ms: float = 500.0,
    ) -> None:
        self.active = active
        self.compare_and_swap = compare_and_swap
        self.build = build
        self.validate = validate
        self.telemetry = telemetry
        self.recall_threshold = recall_threshold
        self.ndcg_threshold = ndcg_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.lock = Lock()

    def run(self, projection: str, candidate: str, *, online_slo_healthy: bool) -> RebuildResult:
        if not online_slo_healthy:
            return RebuildResult(candidate, self.active(projection), False, "online_slo_degraded")
        if not self.lock.acquire(blocking=False):
            return RebuildResult(candidate, self.active(projection), False, "rebuild_in_progress")
        previous = self.active(projection)
        try:
            self.build(candidate)
            quality = self.validate(candidate)
            if not quality.passes(
                recall_threshold=self.recall_threshold,
                ndcg_threshold=self.ndcg_threshold,
                latency_threshold_ms=self.latency_threshold_ms,
            ):
                self.telemetry.result(degraded_reason="quality_gate_failed", result_count=0)
                return RebuildResult(candidate, previous, False, "quality_gate_failed")
            if not self.compare_and_swap(projection, previous, candidate):
                return RebuildResult(candidate, previous, False, "pointer_swap_conflict")
            return RebuildResult(candidate, previous, True)
        except Exception:
            self.telemetry.result(degraded_reason="rebuild_failed", result_count=0)
            return RebuildResult(candidate, previous, False, "rebuild_failed")
        finally:
            self.lock.release()
