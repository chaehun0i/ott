"""Allowlisted, bounded and provider-neutral HTTP ingestion adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from threading import BoundedSemaphore
from time import sleep
from urllib.parse import urlparse

import httpx

from ott_feed.ingestion.application.resilience import ProviderCircuit
from ott_feed.ingestion.domain.errors import IngestionError, ProviderTransientError
from ott_feed.ingestion.ports import ProviderPage, ProviderRecordEnvelope

RETRYABLE_STATUS = frozenset({429, 502, 503, 504})


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("provider URL must be credential-free HTTPS")
    port = parsed.port or 443
    return f"https://{parsed.hostname}:{port}"


class ProviderAdapterRegistry:
    def __init__(self, adapters: Mapping[str, HttpProviderAdapter] | None = None) -> None:
        self._adapters = dict(adapters or {})

    def register(self, provider_id: str, adapter: HttpProviderAdapter) -> None:
        if not provider_id or provider_id in self._adapters:
            raise ValueError("provider adapter ID must be non-empty and unique")
        self._adapters[provider_id] = adapter

    def resolve(self, provider_id: str) -> HttpProviderAdapter:
        try:
            return self._adapters[provider_id]
        except KeyError as exc:
            raise IngestionError("PROVIDER_NOT_CONFIGURED", "provider is not configured") from exc


class HttpProviderAdapter:
    def __init__(
        self,
        *,
        provider_id: str,
        url: str,
        allowed_origins: frozenset[str],
        credential: Callable[[], str],
        max_response_bytes: int,
        max_records_per_page: int,
        max_attempts: int = 3,
        max_concurrency: int = 1,
        circuit: ProviderCircuit | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = sleep,
        jitter: Callable[[float], float] = lambda value: value,
    ) -> None:
        origin = _origin(url)
        if origin not in allowed_origins:
            raise ValueError("provider origin is not allowlisted")
        if max_response_bytes <= 0 or max_records_per_page <= 0 or max_attempts <= 0:
            raise ValueError("provider bounds must be positive")
        self.provider_id = provider_id
        self.url = url
        self.max_response_bytes = max_response_bytes
        self.max_records_per_page = max_records_per_page
        self.max_attempts = max_attempts
        self.credential = credential
        self.circuit = circuit or ProviderCircuit()
        self.bulkhead = BoundedSemaphore(max_concurrency)
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(5.0, connect=0.3, read=4.0),
            follow_redirects=False,
            trust_env=False,
        )
        self.sleeper = sleeper
        self.jitter = jitter

    def fetch_page(self, cursor: str | None, limit: int) -> ProviderPage:
        if limit <= 0 or limit > self.max_records_per_page:
            raise ValueError("page limit exceeds configured bound")
        self.circuit.before_call()
        if not self.bulkhead.acquire(blocking=False):
            raise ProviderTransientError("PROVIDER_BULKHEAD_FULL", "provider capacity is full")
        try:
            return self._attempt(cursor, limit)
        finally:
            self.bulkhead.release()

    def _attempt(self, cursor: str | None, limit: int) -> ProviderPage:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.get(
                    self.url,
                    params={"cursor": cursor or "", "limit": limit},
                    headers={
                        "authorization": f"Bearer {self.credential()}",
                        "accept": "application/json",
                    },
                )
                if 300 <= response.status_code < 400:
                    raise IngestionError("PROVIDER_REDIRECT_REJECTED", "provider redirect rejected")
                if len(response.content) > self.max_response_bytes:
                    raise IngestionError(
                        "PROVIDER_RESPONSE_TOO_LARGE", "provider response too large"
                    )
                if response.status_code in RETRYABLE_STATUS:
                    raise ProviderTransientError(
                        "PROVIDER_RATE_LIMITED"
                        if response.status_code == 429
                        else "PROVIDER_UNAVAILABLE",
                        "provider returned a retryable status",
                    )
                response.raise_for_status()
                page = self._decode(response)
                self.circuit.record(True)
                return page
            except (httpx.TimeoutException, httpx.NetworkError, ProviderTransientError) as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    retry_after = 0.0
                    if "response" in locals() and response.status_code == 429:
                        try:
                            retry_after = min(5.0, float(response.headers.get("retry-after", "0")))
                        except ValueError:
                            retry_after = 0.0
                    self.sleeper(max(retry_after, self.jitter(0.1 * 2 ** (attempt - 1))))
                    continue
                self.circuit.record(False)
        raise ProviderTransientError(
            "PROVIDER_UNAVAILABLE", "provider attempts exhausted"
        ) from last_error

    def _decode(self, response: httpx.Response) -> ProviderPage:
        try:
            payload = response.json()
            records = payload["records"]
            request_id = payload["request_id"]
            next_cursor = payload.get("next_cursor")
            if not isinstance(records, list) or len(records) > self.max_records_per_page:
                raise ValueError("invalid record list")
            envelopes = tuple(
                ProviderRecordEnvelope(
                    str(item["id"]),
                    httpx.Response(200, json=item["payload"]).content,
                    datetime.now(UTC),
                )
                for item in records
                if isinstance(item, dict)
            )
            if len(envelopes) != len(records) or not isinstance(request_id, str):
                raise ValueError("invalid provider record")
            return ProviderPage(
                envelopes, str(next_cursor) if next_cursor is not None else None, request_id
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IngestionError(
                "PROVIDER_CONTRACT_INVALID", "provider response is invalid"
            ) from exc
