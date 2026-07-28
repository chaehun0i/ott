"""Provider-neutral privacy-bounded HTTP embedding adapter."""

from __future__ import annotations

from collections.abc import Sequence
from threading import BoundedSemaphore
from urllib.parse import urlparse

import httpx

from ott_feed.search.application.resilience import EmbeddingCircuit
from ott_feed.search.domain.errors import EmbeddingUnavailable


class HttpEmbeddingAdapter:
    def __init__(
        self,
        *,
        url: str,
        model: str,
        dimension: int,
        allowed_hosts: frozenset[str],
        circuit: EmbeddingCircuit | None = None,
        max_concurrency: int = 4,
        client: httpx.Client | None = None,
    ) -> None:
        host = urlparse(url).hostname
        if host is None or host not in allowed_hosts:
            raise ValueError("embedding host is not allowlisted")
        self.url = url
        self.model = model
        self.dimension = dimension
        self.circuit = circuit or EmbeddingCircuit()
        self.bulkhead = BoundedSemaphore(max_concurrency)
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(1.5, connect=0.3),
            follow_redirects=False,
            trust_env=False,
        )

    def embed(self, text: str) -> Sequence[float]:
        if not text.strip():
            raise ValueError("embedding input must not be empty")
        self.circuit.before_call()
        if not self.bulkhead.acquire(blocking=False):
            raise EmbeddingUnavailable("SEARCH_EMBEDDING_BULKHEAD_FULL")
        try:
            response = self.client.post(
                self.url,
                json={"model": self.model, "input": text},
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            vector = payload.get("embedding")
            returned_model = payload.get("model")
            if returned_model != self.model or not isinstance(vector, list):
                raise EmbeddingUnavailable("SEARCH_EMBEDDING_CONTRACT_INVALID")
            values = [float(value) for value in vector]
            if len(values) != self.dimension:
                raise EmbeddingUnavailable("SEARCH_EMBEDDING_DIMENSION_MISMATCH")
            self.circuit.record(True)
            return values
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            self.circuit.record(False)
            raise EmbeddingUnavailable() from exc
        finally:
            self.bulkhead.release()
