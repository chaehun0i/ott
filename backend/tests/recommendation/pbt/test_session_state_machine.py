from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ott_feed.recommendation.application.sessions import RecommendationSession
from ott_feed.recommendation.domain.models import ConditionKind, Locale, RecommendationIntent


class SessionMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.session = RecommendationSession(
            "s", "owner", 0, 0, RecommendationIntent(Locale.EN, ())
        )
        self.key = 0

    @rule()
    def patch(self) -> None:
        self.key += 1
        self.session = self.session.patch(
            {ConditionKind.GENRE: "comedy"}, self.session.version, f"k{self.key}"
        )

    @rule()
    def reset(self) -> None:
        self.key += 1
        self.session = self.session.reset(self.session.version, f"k{self.key}")

    @invariant()
    def versions_are_monotonic(self) -> None:
        assert self.session.version == self.key
        assert self.session.epoch <= self.session.version


TestSessionMachine = SessionMachine.TestCase
