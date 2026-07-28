"""Typed U03 search configuration with fail-fast safety checks."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_EMBEDDING_URL = "http://embedding.invalid/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "multilingual-v1"


@dataclass(frozen=True, slots=True)
class SearchSettings:
    embedding_url: str = DEFAULT_EMBEDDING_URL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_dimension: int = 768
    connect_timeout_seconds: float = 0.3
    total_timeout_seconds: float = 1.5
    max_concurrency: int = 4
    circuit_window: int = 20
    circuit_failure_ratio: float = 0.5
    circuit_open_seconds: float = 30.0
    half_open_probes: int = 2
    rrf_k: int = 60
    recall_at_10: float = 0.85
    ndcg_at_10: float = 0.80
    cursor_key_file: str = ""
    cursor_previous_key_file: str = ""

    def __post_init__(self) -> None:
        if not self.embedding_url.startswith(("http://", "https://")):
            raise ValueError("embedding_url must be HTTP(S)")
        if self.embedding_dimension <= 0 or self.max_concurrency <= 0:
            raise ValueError("embedding dimension and concurrency must be positive")
        if not 0 < self.circuit_failure_ratio <= 1:
            raise ValueError("circuit_failure_ratio must be within (0, 1]")
        if not 0 <= self.recall_at_10 <= 1 or not 0 <= self.ndcg_at_10 <= 1:
            raise ValueError("quality thresholds must be within [0, 1]")

    @classmethod
    def from_environment(cls) -> SearchSettings:
        return cls(
            embedding_url=os.getenv("EMBEDDING_URL", DEFAULT_EMBEDDING_URL),
            embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "768")),
            cursor_key_file=os.getenv("SEARCH_CURSOR_KEY_FILE", ""),
            cursor_previous_key_file=os.getenv("SEARCH_CURSOR_PREVIOUS_KEY_FILE", ""),
        )
