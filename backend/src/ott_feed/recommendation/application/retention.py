"""Bounded retention planning."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetentionBatch:
    ids: tuple[str, ...]
    next_cursor: str | None


def plan_retention(ids: tuple[str, ...], limit: int = 500) -> RetentionBatch:
    bounded = ids[: min(max(limit, 1), 500)]
    return RetentionBatch(bounded, bounded[-1] if bounded else None)
