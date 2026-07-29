"""Synchronous bounded recommendation pipeline."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from ott_feed.recommendation.application.diversity import diversify
from ott_feed.recommendation.application.eligibility import eligible_candidates
from ott_feed.recommendation.application.evidence import build_evidence
from ott_feed.recommendation.application.grounding import assemble_safe_item
from ott_feed.recommendation.application.intent import deterministic_intent, merge_intent
from ott_feed.recommendation.application.ranking import rank_candidates
from ott_feed.recommendation.domain.errors import RecommendationError, unavailable
from ott_feed.recommendation.domain.models import (
    ApprovedCandidate,
    AtomicClaim,
    ConditionKind,
    DegradedReason,
    FeatureContext,
    Locale,
    RecommendationResponse,
    ValidationState,
)
from ott_feed.recommendation.domain.policies import DiversityPolicy, ScorePolicy
from ott_feed.recommendation.ports import AIProviderPort


class RecommendationOrchestrator:
    def __init__(
        self,
        ai: AIProviderPort | None = None,
        monotonic: Callable[[], float] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        import time

        self.ai = ai
        self.monotonic = monotonic or time.monotonic
        self.now = now or (lambda: datetime.now(UTC))

    def recommend(
        self,
        request_id: str,
        text: str,
        locale: Locale,
        candidates: tuple[ApprovedCandidate, ...] | None,
        features: FeatureContext | None = None,
        validation: Mapping[str, Mapping[str, ValidationState]] | None = None,
    ) -> RecommendationResponse:
        started = self.monotonic()
        intent = deterministic_intent(text, locale)
        degraded: list[DegradedReason] = []
        if self.ai is not None:
            try:
                result = self.ai.interpret({"text": text, "locale": locale.value}, 2_750)
                conditions = result.get("conditions", {})
                if isinstance(conditions, Mapping):
                    patch = {
                        ConditionKind(str(key)): str(value)
                        for key, value in conditions.items()
                        if str(key) in {kind.value for kind in ConditionKind}
                    }
                    intent = merge_intent(intent, patch)
            except (RecommendationError, ValueError):
                degraded.append(DegradedReason.AI_UNAVAILABLE)
        else:
            degraded.append(DegradedReason.AI_UNAVAILABLE)
        if candidates is None:
            raise unavailable("catalog_unavailable", "approved catalog unavailable")
        context = features or FeatureContext()
        if not context.consented:
            degraded.append(DegradedReason.NON_PERSONALIZED)
        eligible = eligible_candidates(candidates[:1000], intent)
        ranked = rank_candidates(eligible, intent, context, ScorePolicy(), 500)
        selected, _reserve = diversify(ranked, DiversityPolicy(), 20)
        items = []
        required = ("approved", "available", "hard_conditions", "evidence")
        for ranked_item in selected:
            item_states = (validation or {}).get(ranked_item.candidate.content_id, {})
            if not all(item_states.get(name) is ValidationState.PASSED for name in required):
                continue
            evidence = build_evidence(ranked_item.candidate)
            claims: tuple[AtomicClaim, ...] = ()
            items.append(assemble_safe_item(ranked_item, evidence, claims, locale))
        if (self.monotonic() - started) * 1000 > 10_000:
            raise unavailable("recommendation_timeout", "recommendation deadline exceeded")
        return RecommendationResponse(
            request_id,
            intent,
            tuple(items),
            self.now(),
            tuple(dict.fromkeys(degraded)),
            bool(intent.conflicts),
        )
