import httpx
import pytest

from ott_feed.recommendation.adapters.ai import HTTPAIProvider
from ott_feed.recommendation.application.evidence import build_evidence
from ott_feed.recommendation.application.grounding import assemble_safe_item
from ott_feed.recommendation.application.resilience import AICircuit, UsageGuard
from ott_feed.recommendation.domain.errors import RecommendationError
from ott_feed.recommendation.domain.models import AtomicClaim, Locale, RankedCandidate, ScoreProof
from tests.recommendation.unit.test_ranking_validation import candidate


def test_ai_adapter_accepts_schema_and_rejects_redirect() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"conditions": {"genre": "comedy"}})

    provider = HTTPAIProvider(
        "https://ai.example/v1",
        "secret",
        httpx.Client(transport=httpx.MockTransport(handler)),
        AICircuit(),
        UsageGuard(10),
    )
    assert provider.interpret({"text": "comedy"}, 100)["conditions"] == {"genre": "comedy"}

    redirect = HTTPAIProvider(
        "https://ai.example/v1",
        "secret",
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(302, headers={"location": "https://evil.example"})
            )
        ),
        AICircuit(),
        UsageGuard(10),
    )
    with pytest.raises(RecommendationError, match="bounds"):
        redirect.interpret({}, 100)


def test_circuit_and_usage_fail_closed() -> None:
    circuit = AICircuit(window=2, failure_ratio=0.5)
    circuit.record(False)
    circuit.record(True)
    with pytest.raises(RecommendationError, match="circuit"):
        circuit.allow()
    with pytest.raises(RecommendationError, match="budget"):
        UsageGuard(1).reserve(2)


def test_failed_cross_candidate_claim_never_leaks() -> None:
    value = candidate("a")
    ranked = RankedCandidate(value, ScoreProof(1, 0, 0, 0, 0), 0)
    evidence = build_evidence(value)
    unsafe = AtomicClaim("b", "m1", "synopsis", "fabricated")
    item = assemble_safe_item(ranked, evidence, (unsafe,), Locale.EN)
    assert item.summary == "safe synopsis"
    assert "fabricated" not in item.summary
