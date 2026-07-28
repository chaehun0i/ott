from collections.abc import Callable

import httpx
import pytest

from ott_feed.ingestion.adapters.providers.http import (
    HttpProviderAdapter,
    ProviderAdapterRegistry,
)
from ott_feed.ingestion.application.resilience import CircuitState, ProviderCircuit
from ott_feed.ingestion.domain.errors import IngestionError, ProviderTransientError

URL = "https://provider.example/v1/content"
ORIGINS = frozenset({"https://provider.example:443"})


def adapter(
    handler: Callable[[httpx.Request], httpx.Response],
    **changes: object,
) -> HttpProviderAdapter:
    values: dict[str, object] = {
        "provider_id": "provider-1",
        "url": URL,
        "allowed_origins": ORIGINS,
        "credential": lambda: "test-token",
        "max_response_bytes": 1_024,
        "max_records_per_page": 10,
        "client": httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
        "sleeper": lambda _: None,
    }
    values.update(changes)
    return HttpProviderAdapter(**values)  # type: ignore[arg-type]


def test_successful_page_uses_bounded_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={"request_id": "r-1", "records": [{"id": "p-1", "payload": {"x": 1}}]},
        )

    page = adapter(handler).fetch_page(None, 10)
    assert page.request_id == "r-1"
    assert page.records[0].provider_record_id == "p-1"


@pytest.mark.parametrize(
    ("handler", "code"),
    [
        (lambda _: httpx.Response(302, headers={"location": "https://evil.example"}), "REDIRECT"),
        (lambda _: httpx.Response(200, content=b"x" * 1_025), "TOO_LARGE"),
        (lambda _: httpx.Response(200, json={"records": []}), "CONTRACT_INVALID"),
    ],
)
def test_redirect_size_and_contract_fail_closed(
    handler: Callable[[httpx.Request], httpx.Response], code: str
) -> None:
    with pytest.raises(IngestionError) as raised:
        adapter(handler).fetch_page(None, 10)
    assert code in raised.value.code


def test_rate_limit_honors_retry_after_and_then_succeeds() -> None:
    calls = 0
    waits: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"retry-after": "2"})
        return httpx.Response(200, json={"request_id": "r", "records": []})

    page = adapter(handler, sleeper=waits.append).fetch_page(None, 1)
    assert page.records == ()
    assert waits == [2.0]


def test_timeout_opens_provider_scoped_circuit() -> None:
    circuit = ProviderCircuit(window=1, failure_ratio=1, open_seconds=30)

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = adapter(timeout, max_attempts=1, circuit=circuit)
    with pytest.raises(ProviderTransientError):
        client.fetch_page(None, 1)
    assert circuit.state is CircuitState.OPEN
    with pytest.raises(ProviderTransientError, match="circuit"):
        client.fetch_page(None, 1)


def test_registry_and_origin_require_explicit_configuration() -> None:
    client = adapter(lambda _: httpx.Response(200, json={"request_id": "r", "records": []}))
    registry = ProviderAdapterRegistry()
    registry.register("provider-1", client)
    assert registry.resolve("provider-1") is client
    with pytest.raises(IngestionError):
        registry.resolve("missing")
    with pytest.raises(ValueError, match="allowlisted"):
        adapter(lambda _: httpx.Response(200), allowed_origins=frozenset())
