"""Optimistic conversational recommendation session state."""

from __future__ import annotations

from dataclasses import dataclass

from ott_feed.recommendation.application.intent import merge_intent
from ott_feed.recommendation.domain.errors import invalid
from ott_feed.recommendation.domain.models import ConditionKind, RecommendationIntent


@dataclass(frozen=True, slots=True)
class RecommendationSession:
    session_id: str
    owner_id: str
    epoch: int
    version: int
    intent: RecommendationIntent
    last_idempotency_key: str | None = None

    def patch(
        self,
        values: dict[ConditionKind, str | None],
        expected_version: int,
        idempotency_key: str,
    ) -> RecommendationSession:
        if self.last_idempotency_key == idempotency_key:
            return self
        if expected_version != self.version:
            raise invalid("session_conflict", "session version conflict")
        return RecommendationSession(
            self.session_id,
            self.owner_id,
            self.epoch,
            self.version + 1,
            merge_intent(self.intent, values),
            idempotency_key,
        )

    def reset(self, expected_version: int, idempotency_key: str) -> RecommendationSession:
        if self.last_idempotency_key == idempotency_key:
            return self
        if expected_version != self.version:
            raise invalid("session_conflict", "session version conflict")
        return RecommendationSession(
            self.session_id,
            self.owner_id,
            self.epoch + 1,
            self.version + 1,
            RecommendationIntent(self.intent.locale, ()),
            idempotency_key,
        )
