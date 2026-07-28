"""Stable U04 domain error families."""

from __future__ import annotations


class IngestionError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class IllegalTransition(IngestionError):
    def __init__(self, message: str) -> None:
        super().__init__("ING_ILLEGAL_TRANSITION", message)


class PolicyViolation(IngestionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message)


class ValidationClosureError(IngestionError):
    def __init__(self, message: str) -> None:
        super().__init__("VAL_CLOSURE", message)


class ProviderTransientError(IngestionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, retryable=True)
