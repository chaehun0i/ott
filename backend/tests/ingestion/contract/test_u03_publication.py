from datetime import UTC, datetime

import pytest

from ott_feed.catalog.application.commands import PassedValidationCommand
from ott_feed.catalog.domain.models import (
    CatalogContent,
    CatalogSource,
    CatalogVersion,
    Localization,
)
from ott_feed.ingestion.adapters.catalog import U03CatalogPublicationAdapter
from ott_feed.ingestion.application.publication import PublicationDispatcher
from ott_feed.ingestion.domain.errors import IngestionError
from ott_feed.ingestion.domain.models import DecisionState, PublicationReceipt, ValidationDecision

NOW = datetime(2026, 7, 28, tzinfo=UTC)


class FakeU03Service:
    def __init__(self) -> None:
        self.commands: list[PassedValidationCommand] = []

    def execute(self, command: PassedValidationCommand) -> CatalogVersion:
        self.commands.append(command)
        return CatalogVersion(7)


def content() -> CatalogContent:
    return CatalogContent(
        "content-1",
        "movie",
        frozenset({"comedy"}),
        NOW,
        60,
        0.5,
        {"ko-KR": Localization("ko-KR", "제목", "요약")},
        (),
        CatalogSource("provider", "record", "license", NOW),
    )


def test_adapter_maps_u04_decision_to_existing_u03_command() -> None:
    service = FakeU03Service()
    adapter = U03CatalogPublicationAdapter(service, lambda _: content(), lambda _: None)
    decision = ValidationDecision(
        "decision",
        "run",
        "content-1",
        "rules",
        DecisionState.PASSED_PENDING_PUBLICATION,
        publication_key="key",
    )
    stores = MemoryStores()
    receipt = PublicationDispatcher(adapter, stores, stores).dispatch(decision, NOW)
    assert receipt.catalog_version == 7
    assert service.commands[0].decision_id == "decision"
    assert service.commands[0].content_id == "content-1"


class MemoryStores:
    def __init__(self) -> None:
        self.receipts: dict[str, PublicationReceipt] = {}
        self.acknowledgements: list[tuple[str, int]] = []

    def get(self, key: str) -> PublicationReceipt | None:
        return self.receipts.get(key)

    def save(self, receipt: PublicationReceipt) -> None:
        self.receipts.setdefault(receipt.publication_key, receipt)

    def acknowledge(self, decision_id: str, version: int, _: datetime) -> None:
        self.acknowledgements.append((decision_id, version))


class UnknownPort:
    def __init__(self, committed: bool) -> None:
        self.committed = committed
        self.calls = 0

    def execute(self, _command) -> int:  # type: ignore[no-untyped-def]
        self.calls += 1
        raise TimeoutError

    def reconcile(self, _decision_id: str) -> int | None:
        return 9 if self.committed else None


@pytest.mark.parametrize("committed", [False, True])
def test_timeout_before_or_after_commit_reuses_same_decision(committed: bool) -> None:
    stores = MemoryStores()
    port = UnknownPort(committed)
    decision = ValidationDecision(
        "decision",
        "run",
        "merged",
        "rules",
        DecisionState.PASSED_PENDING_PUBLICATION,
        publication_key="key",
    )
    dispatcher = PublicationDispatcher(port, stores, stores)
    if committed:
        receipt = dispatcher.dispatch(decision, NOW)
        assert receipt.catalog_version == 9
        assert len(stores.receipts) == 1
    else:
        with pytest.raises(IngestionError) as raised:
            dispatcher.dispatch(decision, NOW)
        assert raised.value.retryable and not stores.receipts
