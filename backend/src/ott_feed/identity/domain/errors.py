"""Safe U02 domain errors with stable machine-readable codes."""

from dataclasses import dataclass


@dataclass(slots=True)
class IdentityError(Exception):
    code: str
    message_key: str
    retryable: bool = False

    def __str__(self) -> str:
        return self.code


def invalid(code: str, message_key: str) -> IdentityError:
    return IdentityError(code, message_key)


def conflict(code: str, message_key: str) -> IdentityError:
    return IdentityError(code, message_key)


def denied(
    code: str = "access_denied", message_key: str = "identity.access_denied"
) -> IdentityError:
    return IdentityError(code, message_key)


def unavailable(code: str, message_key: str) -> IdentityError:
    return IdentityError(code, message_key, retryable=True)
