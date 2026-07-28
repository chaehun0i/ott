"""Consent-gated, durable and deduplicated behavior feedback intake."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.models import (
    BehaviorEvent,
    BehaviorEventType,
    ConsentLedger,
    ConsentPurpose,
    UserLibrary,
)
from ott_feed.identity.domain.policies import event_fingerprint
from ott_feed.identity.ports import CatalogReference, SecretCryptography

EXPLICIT_EVENTS = {
    BehaviorEventType.SAVE,
    BehaviorEventType.UNSAVE,
    BehaviorEventType.RATE,
    BehaviorEventType.UNRATE,
    BehaviorEventType.WATCH_COMPLETE,
}


class FeedbackConsentRepository(Protocol):
    def get(self, key: tuple[str, str]) -> ConsentLedger: ...


class FeedbackBehaviorRepository(Protocol):
    def save_event(self, event: BehaviorEvent, dedup_key: str) -> tuple[UUID, bool]: ...


class FeedbackLibraryRepository(Protocol):
    def get(self, user_id: UUID) -> UserLibrary: ...

    def save(self, library: UserLibrary, expected_version: int | None = None) -> None: ...


class FeedbackJobPublisher(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class FeedbackWork(Protocol):
    consents: FeedbackConsentRepository
    behavior: FeedbackBehaviorRepository
    libraries: FeedbackLibraryRepository
    jobs: FeedbackJobPublisher

    def __enter__(self) -> FeedbackWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class FeedbackService:
    def __init__(
        self,
        uow_factory: Callable[[], FeedbackWork],
        catalog: CatalogReference,
        cryptography: SecretCryptography,
        now: Callable[[], datetime],
    ) -> None:
        self.uow_factory = uow_factory
        self.catalog = catalog
        self.cryptography = cryptography
        self.now = now

    def record(
        self,
        user_id: UUID,
        content_id: str,
        event_type: BehaviorEventType,
        source_surface: str,
        occurred_at: datetime,
        attributes: Mapping[str, str | int | bool],
        idempotency_key: str | None,
        recommendation_version: str | None = None,
    ) -> tuple[UUID, bool]:
        if not self.catalog.content_exists(content_id):
            from ott_feed.identity.domain.errors import invalid

            raise invalid("content_not_found", "identity.content_not_found")
        received_at = self.now()
        _, subject_index = self.cryptography.blind_index("behavior-subject", str(user_id))
        subject_id = subject_index.hex()
        with self.uow_factory() as work:
            consent = work.consents.get(("user", str(user_id))).granted(
                ConsentPurpose.PERSONALIZATION
            )
            typed_attributes = dict(attributes)
            fingerprint = event_fingerprint(
                subject_id,
                content_id,
                event_type.value,
                occurred_at,
                typed_attributes,
            )
            dedup_key = idempotency_key or fingerprint
            event = BehaviorEvent(
                subject_id=subject_id,
                content_id=content_id,
                event_type=event_type,
                occurred_at=occurred_at,
                received_at=received_at,
                source_surface=source_surface,
                recommendation_version=recommendation_version,
                attributes=typed_attributes,
                consent_decision_id=consent.id,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            event_id, created = work.behavior.save_event(event, dedup_key)
            if not created:
                work.commit()
                return event_id, False
            if event_type in EXPLICIT_EVENTS:
                self._apply_explicit(work, user_id, event)
                job_type = "identity.feature.explicit-refresh"
            else:
                job_type = "identity.feature.implicit-event"
            work.jobs.enqueue(
                job_type,
                {
                    "eventId": str(event.id),
                    "userId": str(user_id),
                    "consentVersion": consent.sequence,
                },
                "normal",
            )
            work.commit()
            return event_id, True

    @staticmethod
    def _apply_explicit(work: FeedbackWork, user_id: UUID, event: BehaviorEvent) -> None:
        library = work.libraries.get(user_id)
        expected = library.row_version
        if event.event_type == BehaviorEventType.SAVE:
            library.save(event.content_id, event.received_at)
        elif event.event_type == BehaviorEventType.UNSAVE:
            library.unsave(event.content_id)
        elif event.event_type == BehaviorEventType.RATE:
            library.rate(event.content_id, int(event.attributes.get("rating", 0)))
        elif event.event_type == BehaviorEventType.UNRATE:
            library.unrate(event.content_id)
        elif event.event_type == BehaviorEventType.WATCH_COMPLETE:
            library.complete_watch(event.content_id, event.occurred_at)
        work.libraries.save(library, expected)
