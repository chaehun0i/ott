import httpx
import pytest

from ott_feed.recommendation.adapters.ai import HTTPAIProvider
from ott_feed.recommendation.application.orchestrator import RecommendationOrchestrator
from ott_feed.recommendation.application.recovery import (
    RecoverySnapshot,
    deterministic_reentry_allowed,
)
from ott_feed.recommendation.application.resilience import AICircuit, UsageGuard
from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import Locale

pytestmark = pytest.mark.integration


def test_ai_timeout_degrades_without_error_body_leakage() -> None:
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider-secret-body")

    provider = HTTPAIProvider(
        "https://ai.example",
        "secret",
        httpx.Client(transport=httpx.MockTransport(timeout)),
        AICircuit(),
        UsageGuard(10),
    )
    response = RecommendationOrchestrator(ai=provider).recommend(
        "r", "comedy", Locale.EN, (), validation={}
    )
    assert "ai_unavailable" in {reason.value for reason in response.degraded_reasons}


def test_required_catalog_failure_remains_closed() -> None:
    with pytest.raises(RecommendationError, match="catalog unavailable"):
        RecommendationOrchestrator().recommend("r", "comedy", Locale.EN, None)


def test_restore_contract_failure_blocks_reentry() -> None:
    snapshot = RecoverySnapshot(True, True, True, False, True, True, True, True)
    assert not deterministic_reentry_allowed(snapshot)
