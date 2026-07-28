from datetime import UTC, datetime

import pytest

from ott_feed.ingestion.config import IngestionSettings
from ott_feed.ingestion.ports import ProviderPage, ProviderRecordEnvelope


def test_default_settings_match_approved_single_host_budgets() -> None:
    settings = IngestionSettings()
    assert settings.worker_pool_size == 5
    assert settings.api_pool_size == 2
    assert settings.global_provider_concurrency == 4
    assert settings.per_provider_concurrency == 1
    assert settings.total_timeout_seconds == 5.0
    assert settings.pending_publication_max_seconds == 300


def test_environment_settings_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("U04_CLAIM_BATCH_SIZE", "25")
    monkeypatch.setenv("U04_CIRCUIT_FAILURE_RATIO", "0.25")
    settings = IngestionSettings.from_environment()
    assert settings.claim_batch_size == 25
    assert settings.circuit_failure_ratio == 0.25


@pytest.mark.parametrize(
    "values",
    [
        {"worker_pool_size": 0},
        {"global_provider_concurrency": 1, "per_provider_concurrency": 2},
        {"connect_timeout_seconds": 6.0, "total_timeout_seconds": 5.0},
        {"circuit_failure_ratio": 0.0},
    ],
)
def test_invalid_settings_fail_fast(values: dict[str, int | float]) -> None:
    with pytest.raises(ValueError):
        IngestionSettings(**values)  # type: ignore[arg-type]


def test_provider_page_is_immutable_and_bounded_by_transport_contract() -> None:
    record = ProviderRecordEnvelope("provider-record", b"{}", datetime(2026, 1, 1, tzinfo=UTC))
    page = ProviderPage((record,), "next", "request-1")
    assert page.records == (record,)
    assert page.next_cursor == "next"
