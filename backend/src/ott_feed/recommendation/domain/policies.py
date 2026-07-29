"""Versioned deterministic U05 policy values."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScorePolicy:
    version: str = "score-v1"
    request_fit: float = 0.45
    affinity: float = 0.20
    freshness: float = 0.15
    popularity: float = 0.10
    novelty: float = 0.10

    def __post_init__(self) -> None:
        weights = (
            self.request_fit,
            self.affinity,
            self.freshness,
            self.popularity,
            self.novelty,
        )
        if any(weight < 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("score weights must be non-negative and sum to one")


@dataclass(frozen=True, slots=True)
class DiversityPolicy:
    version: str = "diversity-v1"
    max_per_genre: int = 3
    max_per_ott: int = 4
    max_per_franchise: int = 1

    def __post_init__(self) -> None:
        if min(self.max_per_genre, self.max_per_ott, self.max_per_franchise) <= 0:
            raise ValueError("diversity caps must be positive")
