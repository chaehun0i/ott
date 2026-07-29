"""Stable U05 domain failures."""

from dataclasses import dataclass


@dataclass(slots=True)
class RecommendationError(Exception):
    code: str
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


def invalid(code: str, message: str) -> RecommendationError:
    return RecommendationError(code, message)


def unavailable(code: str, message: str) -> RecommendationError:
    return RecommendationError(code, message, True)
