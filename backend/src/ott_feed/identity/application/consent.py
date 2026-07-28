"""Versioned consent, explicit guest linking and withdrawal cleanup orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.models import (
    ConsentDecision,
    ConsentLedger,
    ConsentPurpose,
    ConsentValue,
    GuestLinkAuthorization,
)


class ConsentRepositoryPort(Protocol):
    def get(self, key: tuple[str, str]) -> ConsentLedger: ...

    def save(self, ledger: ConsentLedger, expected_version: int | None = None) -> None: ...


class ConsentJobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class ConsentWork(Protocol):
    consents: ConsentRepositoryPort
    jobs: ConsentJobPublisher

    def __enter__(self) -> ConsentWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class ConsentService:
    def __init__(self, uow_factory: Callable[[], ConsentWork], now: Callable[[], datetime]) -> None:
        self.uow_factory = uow_factory
        self.now = now

    def decide_personalization(
        self,
        user_id: UUID,
        value: ConsentValue,
        policy_version: str,
        notice_version: str,
        locale: str,
        source: str,
    ) -> ConsentDecision:
        key = ("user", str(user_id))
        with self.uow_factory() as work:
            ledger = work.consents.get(key)
            expected = ledger.row_version
            decision = ledger.decide(
                ConsentPurpose.PERSONALIZATION,
                value,
                policy_version,
                notice_version,
                locale,
                source,
                self.now(),
            )
            work.consents.save(ledger, expected)
            if value == ConsentValue.WITHDRAWN:
                work.jobs.enqueue(
                    "identity.consent.withdrawal-cleanup",
                    {
                        "userId": str(user_id),
                        "consentDecisionId": str(decision.id),
                        "consentVersion": decision.sequence,
                    },
                    "high",
                )
            work.commit()
            return decision

    def current_personalization(self, user_id: UUID) -> ConsentDecision:
        with self.uow_factory() as work:
            return work.consents.get(("user", str(user_id))).granted(ConsentPurpose.PERSONALIZATION)

    def authorize_guest_link(
        self,
        user_id: UUID,
        guest_subject_id: str,
        event_from: datetime,
        event_until: datetime,
        policy_version: str,
    ) -> GuestLinkAuthorization:
        authorization = GuestLinkAuthorization(
            guest_subject_id,
            user_id,
            event_from,
            event_until,
            policy_version,
            granted_at=self.now(),
        )
        with self.uow_factory() as work:
            work.jobs.enqueue(
                "identity.guest.link",
                {
                    "authorizationId": str(authorization.id),
                    "guestSubjectId": guest_subject_id,
                    "userId": str(user_id),
                    "eventFrom": event_from.isoformat(),
                    "eventUntil": event_until.isoformat(),
                    "policyVersion": policy_version,
                },
                "normal",
            )
            work.commit()
        return authorization
