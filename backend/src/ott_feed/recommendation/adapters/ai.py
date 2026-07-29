"""Provider-neutral bounded AI HTTP adapter."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ott_feed.recommendation.application.resilience import AICircuit, UsageGuard
from ott_feed.recommendation.domain.errors import RecommendationError, unavailable


class IntentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conditions: dict[str, str] = Field(max_length=32)


class ClaimSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_id: str
    metadata_version: str
    field_path: str
    text: str = Field(min_length=1, max_length=1000)


class DraftSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[ClaimSchema] = Field(max_length=1280)


class HTTPAIProvider:
    def __init__(
        self,
        endpoint: str,
        credential: str,
        client: httpx.Client,
        circuit: AICircuit,
        usage: UsageGuard,
        max_response_bytes: int = 262_144,
    ) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError("AI endpoint must be an allowlisted HTTPS origin")
        self.endpoint = endpoint.rstrip("/")
        self.credential = credential
        self.client = client
        self.circuit = circuit
        self.usage = usage
        self.max_response_bytes = max_response_bytes

    def _post(self, operation: str, payload: Mapping[str, object], timeout_ms: int) -> object:
        self.circuit.allow()
        self.usage.reserve(1)
        try:
            response = self.client.post(
                f"{self.endpoint}/{operation}",
                json=dict(payload),
                headers={"Authorization": f"Bearer {self.credential}"},
                timeout=timeout_ms / 1000,
                follow_redirects=False,
            )
            if response.is_redirect or len(response.content) > self.max_response_bytes:
                raise unavailable("ai_response_rejected", "AI response violated bounds")
            response.raise_for_status()
            self.circuit.record(True)
            return response.json()
        except (httpx.HTTPError, ValueError, RecommendationError) as exc:
            self.circuit.record(False)
            if isinstance(exc, RecommendationError):
                raise
            raise unavailable("ai_unavailable", "AI provider unavailable") from exc

    def interpret(self, payload: Mapping[str, object], timeout_ms: int) -> Mapping[str, object]:
        try:
            return IntentSchema.model_validate(
                self._post("intent", payload, timeout_ms)
            ).model_dump()
        except ValidationError as exc:
            raise unavailable("ai_schema_invalid", "AI intent schema invalid") from exc

    def draft(self, payload: Mapping[str, object], timeout_ms: int) -> Mapping[str, object]:
        try:
            return DraftSchema.model_validate(self._post("draft", payload, timeout_ms)).model_dump()
        except ValidationError as exc:
            raise unavailable("ai_schema_invalid", "AI draft schema invalid") from exc
