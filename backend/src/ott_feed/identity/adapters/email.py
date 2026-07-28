"""Provider-neutral email adapters for Local, CI and SMTP-backed Remote use."""

from __future__ import annotations

import smtplib
from collections.abc import Mapping
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(frozen=True, slots=True)
class DeliveredEmail:
    template: str
    recipient: str
    variables: dict[str, str]


class MailSinkEmailAdapter:
    """Local-only sink; values stay in memory and are never emitted to logs."""

    def __init__(self) -> None:
        self.messages: list[DeliveredEmail] = []

    def send(self, template: str, recipient: str, variables: Mapping[str, str]) -> None:
        self.messages.append(DeliveredEmail(template, recipient, dict(variables)))


class FakeEmailAdapter:
    """CI fake that records only the template name, never recipient or variables."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent_templates: list[str] = []

    def send(self, template: str, recipient: str, variables: Mapping[str, str]) -> None:
        del recipient, variables
        if self.fail:
            raise OSError("email provider unavailable")
        self.sent_templates.append(template)


class SmtpEmailAdapter:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.timeout_seconds = timeout_seconds

    def send(self, template: str, recipient: str, variables: Mapping[str, str]) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = self._subject(template)
        message.set_content(self._body(template, variables))
        with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as client:
            client.starttls()
            client.login(self.username, self.password)
            client.send_message(message)

    @staticmethod
    def _subject(template: str) -> str:
        subjects = {
            "verify_email": "OTT Feed email verification",
            "reset_password": "OTT Feed password reset",
        }
        return subjects.get(template, "OTT Feed account notification")

    @staticmethod
    def _body(template: str, variables: Mapping[str, str]) -> str:
        action_url = variables.get("actionUrl", "")
        if template == "verify_email":
            return f"Complete your email verification: {action_url}"
        if template == "reset_password":
            return f"Reset your password: {action_url}"
        return "OTT Feed account notification"
