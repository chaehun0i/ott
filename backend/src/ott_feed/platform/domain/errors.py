"""Safe platform errors that never expose internal provider or credential details."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PlatformError(Exception):
    code: str
    message: str
    status_code: int = 400
    retryable: bool = False
    safe_details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


def conflict(code: str, message: str) -> PlatformError:
    return PlatformError(code, message, status_code=409)


def invalid_state(code: str, message: str) -> PlatformError:
    return PlatformError(code, message, status_code=422)
