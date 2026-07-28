"""Typed ports implemented by U02 through U06 without U07 business coupling."""

from typing import Protocol


class AuthorizedIdentityPort(Protocol):
    def resolve(self, token: str) -> str | None: ...


class HealthContributionPort(Protocol):
    def readiness(self) -> bool: ...


class RestoreSmokeAssertionPort(Protocol):
    def verify(self) -> bool: ...


class AlertPort(Protocol):
    def send(self, severity: str, event_code: str, correlation_id: str) -> None: ...
