from datetime import UTC, datetime

from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ott_feed.ingestion.application.jobs import JobLifecycle, PageOutcome
from ott_feed.ingestion.domain.models import IngestionJob

NOW = datetime(2026, 7, 28, tzinfo=UTC)


class JobReferenceMachine(RuleBasedStateMachine):
    """PBT-U04-10 stateful job model including PBT-U04-12 replay behavior."""

    def __init__(self) -> None:
        super().__init__()
        self.job = IngestionJob("job", "provider", "policy", "start")
        self.lifecycle = JobLifecycle()
        self.job.claim("worker", NOW)
        self.token = self.lifecycle.token(self.job)
        self.expected: set[str] = set()
        self.page = 0

    @rule()
    def apply_new_page(self) -> None:
        record_id = f"record-{self.page}"
        self.lifecycle.apply_page(
            self.job,
            self.token,
            f"page-{self.page}",
            frozenset({record_id}),
            PageOutcome(str(self.page + 1), frozenset({record_id}), frozenset(), frozenset()),
        )
        self.expected.add(record_id)
        self.page += 1

    @rule()
    def replay_last_page(self) -> None:
        if self.page == 0:
            return
        index = self.page - 1
        record_id = f"record-{index}"
        changed = self.lifecycle.apply_page(
            self.job,
            self.token,
            f"page-{index}",
            frozenset({record_id}),
            PageOutcome(str(index + 1), frozenset({record_id}), frozenset(), frozenset()),
        )
        assert not changed

    @invariant()
    def counts_and_cursor_match_reference(self) -> None:
        assert self.job.succeeded_count == len(self.expected)
        assert len(self.job.applied_page_digests) == len(self.expected)
        assert self.job.durable_cursor == (str(self.page) if self.page else None)


TestJobReferenceMachine = JobReferenceMachine.TestCase
