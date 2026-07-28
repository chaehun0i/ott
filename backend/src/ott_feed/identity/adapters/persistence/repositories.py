"""PostgreSQL repository adapters with optimistic concurrency and fail-closed reads."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SqlSession

from ott_feed.identity.adapters.persistence.models import (
    BehaviorEventRow,
    ConsentCurrentRow,
    ConsentDecisionRow,
    CredentialRow,
    DataRightsRequestRow,
    DeletionStepRow,
    EventDeduplicationRow,
    GenrePreferenceRow,
    OAuthLinkRow,
    OttSubscriptionRow,
    RatingRow,
    RoleAssignmentRow,
    SessionRow,
    UserProfileRow,
    UserRow,
    WatchHistoryRow,
    WatchItemRow,
)
from ott_feed.identity.domain.errors import conflict, unavailable
from ott_feed.identity.domain.models import (
    BehaviorEvent,
    BehaviorEventStream,
    BehaviorEventType,
    ConsentDecision,
    ConsentLedger,
    ConsentPurpose,
    ConsentValue,
    Credential,
    DataRightsRequest,
    DataRightsStatus,
    DataRightsType,
    DeletionStep,
    GenrePreferenceState,
    OAuthLink,
    OttSubscriptionState,
    Role,
    Session,
    User,
    UserLibrary,
    UserProfile,
    UserStatus,
    WatchHistoryEntry,
)
from ott_feed.platform.adapters.database import SqlAlchemyOutboxRepository
from ott_feed.platform.domain.models import OutboxJob


def _integrity_conflict(exc: IntegrityError) -> Exception:
    return conflict("persistence_unique_conflict", "identity.conflict")


class SqlAlchemyIdentityRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get_user(self, user_id: UUID) -> User | None:
        row = self.session.get(UserRow, user_id)
        return self._to_domain(row) if row else None

    def find_user_by_email_index(self, version: int, index: bytes) -> User | None:
        row = self.session.scalar(
            select(UserRow).where(
                UserRow.email_blind_index_version == version,
                UserRow.email_blind_index == index,
                UserRow.status != UserStatus.DELETED.value,
            )
        )
        return self._to_domain(row) if row else None

    def find_user_by_oauth(self, provider: str, subject_index: bytes) -> User | None:
        link = self.session.scalar(
            select(OAuthLinkRow).where(
                OAuthLinkRow.provider == provider,
                OAuthLinkRow.provider_subject_index == subject_index,
                OAuthLinkRow.revoked_at.is_(None),
            )
        )
        return self.get_user(link.user_id) if link else None

    def save_user(self, user: User, expected_version: int | None = None) -> None:
        existing = self.session.get(UserRow, user.id)
        try:
            if existing is None:
                self.session.add(
                    UserRow(
                        id=user.id,
                        status=user.status.value,
                        email_ciphertext=user.email_ciphertext,
                        email_blind_index_version=user.email_blind_index_version,
                        email_blind_index=user.email_blind_index,
                        email_verified_at=user.email_verified_at,
                        authorization_version=user.authorization_version,
                        row_version=user.row_version,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                    )
                )
                self.session.flush()
            else:
                version = expected_version if expected_version is not None else existing.row_version
                result = self.session.execute(
                    update(UserRow)
                    .where(UserRow.id == user.id, UserRow.row_version == version)
                    .values(
                        status=user.status.value,
                        email_ciphertext=user.email_ciphertext,
                        email_blind_index_version=user.email_blind_index_version,
                        email_blind_index=user.email_blind_index,
                        email_verified_at=user.email_verified_at,
                        authorization_version=user.authorization_version,
                        row_version=user.row_version,
                        updated_at=user.updated_at,
                    )
                )
                if getattr(result, "rowcount", 0) != 1:
                    raise conflict("optimistic_conflict", "identity.conflict")
            self._replace_children(user)
            self.session.flush()
        except IntegrityError as exc:
            raise _integrity_conflict(exc) from exc

    def _replace_children(self, user: User) -> None:
        self.session.execute(delete(CredentialRow).where(CredentialRow.user_id == user.id))
        self.session.execute(delete(OAuthLinkRow).where(OAuthLinkRow.user_id == user.id))
        self.session.execute(delete(RoleAssignmentRow).where(RoleAssignmentRow.user_id == user.id))
        self.session.add_all(
            CredentialRow(
                id=item.id,
                user_id=user.id,
                password_hash=item.password_hash,
                policy_version=item.policy_version,
                created_at=item.created_at,
                changed_at=item.changed_at,
                disabled_at=item.disabled_at,
            )
            for item in user.credentials
        )
        self.session.add_all(
            OAuthLinkRow(
                id=item.id,
                user_id=user.id,
                provider=item.provider,
                provider_subject_index=item.provider_subject_index,
                verified_email_ciphertext=item.verified_email_ciphertext,
                linked_at=item.linked_at,
                revoked_at=item.revoked_at,
            )
            for item in user.oauth_links
        )
        now = user.updated_at
        self.session.add_all(
            RoleAssignmentRow(
                user_id=user.id,
                role=role.value,
                granted_at=now,
                granted_by=None,
                reason="domain_state",
                revoked_at=None,
            )
            for role in user.roles
        )

    def _to_domain(self, row: UserRow) -> User:
        credentials = self.session.scalars(
            select(CredentialRow).where(CredentialRow.user_id == row.id)
        ).all()
        links = self.session.scalars(
            select(OAuthLinkRow).where(OAuthLinkRow.user_id == row.id)
        ).all()
        roles = self.session.scalars(
            select(RoleAssignmentRow).where(
                RoleAssignmentRow.user_id == row.id, RoleAssignmentRow.revoked_at.is_(None)
            )
        ).all()
        return User(
            id=row.id,
            status=UserStatus(row.status),
            email_ciphertext=row.email_ciphertext,
            email_blind_index_version=row.email_blind_index_version,
            email_blind_index=row.email_blind_index,
            email_verified_at=row.email_verified_at,
            credentials=[
                Credential(
                    id=item.id,
                    password_hash=item.password_hash,
                    policy_version=item.policy_version,
                    created_at=item.created_at,
                    changed_at=item.changed_at,
                    disabled_at=item.disabled_at,
                )
                for item in credentials
            ],
            oauth_links=[
                OAuthLink(
                    id=item.id,
                    provider=item.provider,
                    provider_subject_index=item.provider_subject_index,
                    verified_email_ciphertext=item.verified_email_ciphertext,
                    linked_at=item.linked_at,
                    revoked_at=item.revoked_at,
                )
                for item in links
            ],
            roles={Role(item.role) for item in roles},
            authorization_version=row.authorization_version,
            row_version=row.row_version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SqlAlchemySessionRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def find_by_token_hmac(self, token_hmac: bytes) -> Session | None:
        row = self.session.scalar(select(SessionRow).where(SessionRow.token_hmac == token_hmac))
        return self._to_domain(row) if row else None

    def get(self, session_id: UUID) -> Session | None:
        row = self.session.get(SessionRow, session_id)
        return self._to_domain(row) if row else None

    def save_session(self, session: Session) -> None:
        row = self.session.get(SessionRow, session.id)
        values = {
            "user_id": session.user_id,
            "token_hmac": session.token_hmac,
            "authorization_version": session.authorization_version,
            "device_label": session.device_label[:120],
            "issued_at": session.issued_at,
            "last_seen_at": session.last_seen_at,
            "absolute_expires_at": session.absolute_expires_at,
            "fresh_authenticated_at": session.fresh_authenticated_at,
            "revoked_at": session.revoked_at,
            "revoke_reason": session.revoke_reason,
        }
        if row is None:
            self.session.add(SessionRow(id=session.id, **values))
        else:
            for key, value in values.items():
                setattr(row, key, value)
        self.session.flush()

    def revoke_all(self, user_id: UUID, reason: str, at: datetime) -> int:
        result = self.session.execute(
            update(SessionRow)
            .where(SessionRow.user_id == user_id, SessionRow.revoked_at.is_(None))
            .values(revoked_at=at, revoke_reason=reason)
        )
        return int(getattr(result, "rowcount", 0) or 0)

    @staticmethod
    def _to_domain(row: SessionRow) -> Session:
        return Session(
            id=row.id,
            user_id=row.user_id,
            token_hmac=row.token_hmac,
            authorization_version=row.authorization_version,
            device_label=row.device_label,
            issued_at=row.issued_at,
            last_seen_at=row.last_seen_at,
            absolute_expires_at=row.absolute_expires_at,
            fresh_authenticated_at=row.fresh_authenticated_at,
            revoked_at=row.revoked_at,
            revoke_reason=row.revoke_reason,
        )


class SqlAlchemyProfileRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get(self, user_id: UUID) -> UserProfile | None:
        row = self.session.get(UserProfileRow, user_id)
        if row is None:
            return None
        genres = self.session.scalars(
            select(GenrePreferenceRow).where(GenrePreferenceRow.user_id == user_id)
        ).all()
        providers = self.session.scalars(
            select(OttSubscriptionRow).where(OttSubscriptionRow.user_id == user_id)
        ).all()
        return UserProfile(
            user_id=user_id,
            locale=row.locale,
            genres={item.genre_id: GenrePreferenceState(item.state) for item in genres},
            ott_subscriptions={
                item.provider_id: OttSubscriptionState(item.state) for item in providers
            },
            profile_version=row.profile_version,
            row_version=row.row_version,
        )

    def save(self, profile: UserProfile, expected_version: int | None = None) -> None:
        row = self.session.get(UserProfileRow, profile.user_id)
        if row is None:
            self.session.add(
                UserProfileRow(
                    user_id=profile.user_id,
                    locale=profile.locale,
                    profile_version=profile.profile_version,
                    row_version=profile.row_version,
                )
            )
            self.session.flush()
        else:
            expected = expected_version if expected_version is not None else row.row_version
            result = self.session.execute(
                update(UserProfileRow)
                .where(
                    UserProfileRow.user_id == profile.user_id,
                    UserProfileRow.row_version == expected,
                )
                .values(
                    locale=profile.locale,
                    profile_version=profile.profile_version,
                    row_version=profile.row_version,
                )
            )
            if getattr(result, "rowcount", 0) != 1:
                raise conflict("optimistic_conflict", "identity.conflict")
        self.session.execute(
            delete(GenrePreferenceRow).where(GenrePreferenceRow.user_id == profile.user_id)
        )
        self.session.execute(
            delete(OttSubscriptionRow).where(OttSubscriptionRow.user_id == profile.user_id)
        )
        self.session.add_all(
            GenrePreferenceRow(user_id=profile.user_id, genre_id=key, state=value.value)
            for key, value in profile.genres.items()
        )
        self.session.add_all(
            OttSubscriptionRow(user_id=profile.user_id, provider_id=key, state=value.value)
            for key, value in profile.ott_subscriptions.items()
        )
        self.session.flush()


class SqlAlchemyLibraryRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get(self, user_id: UUID) -> UserLibrary:
        saved = self.session.scalars(
            select(WatchItemRow).where(WatchItemRow.user_id == user_id)
        ).all()
        ratings = self.session.scalars(select(RatingRow).where(RatingRow.user_id == user_id)).all()
        history = self.session.scalars(
            select(WatchHistoryRow).where(WatchHistoryRow.user_id == user_id)
        ).all()
        return UserLibrary(
            user_id=user_id,
            saved={item.content_id: item.saved_at for item in saved},
            ratings={item.content_id: item.rating for item in ratings},
            history={
                item.content_id: WatchHistoryEntry(item.completed, item.last_watched_at)
                for item in history
            },
        )

    def save(self, library: UserLibrary, expected_version: int | None = None) -> None:
        del expected_version
        self.session.execute(delete(WatchItemRow).where(WatchItemRow.user_id == library.user_id))
        self.session.execute(delete(RatingRow).where(RatingRow.user_id == library.user_id))
        self.session.execute(
            delete(WatchHistoryRow).where(WatchHistoryRow.user_id == library.user_id)
        )
        self.session.add_all(
            WatchItemRow(user_id=library.user_id, content_id=content, saved_at=at)
            for content, at in library.saved.items()
        )
        now = datetime.now(UTC)
        self.session.add_all(
            RatingRow(
                user_id=library.user_id,
                content_id=content,
                rating=rating,
                rated_at=now,
                modified_at=now,
            )
            for content, rating in library.ratings.items()
        )
        self.session.add_all(
            WatchHistoryRow(
                user_id=library.user_id,
                content_id=content,
                completed=entry.completed,
                last_watched_at=entry.last_watched_at,
            )
            for content, entry in library.history.items()
        )
        self.session.flush()


class SqlAlchemyConsentRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get(self, key: tuple[str, str]) -> ConsentLedger:
        subject_type, subject_id = key
        try:
            rows = self.session.scalars(
                select(ConsentDecisionRow)
                .where(
                    ConsentDecisionRow.subject_type == subject_type,
                    ConsentDecisionRow.subject_id == subject_id,
                )
                .order_by(ConsentDecisionRow.sequence)
            ).all()
        except Exception as exc:
            raise unavailable(
                "consent_read_failed", "identity.personalization_unavailable"
            ) from exc
        return ConsentLedger(
            subject_id=subject_id,
            subject_type=subject_type,
            decisions=[
                ConsentDecision(
                    id=row.id,
                    subject_id=row.subject_id,
                    subject_type=row.subject_type,
                    purpose=ConsentPurpose(row.purpose),
                    value=ConsentValue(row.decision),
                    policy_version=row.policy_version,
                    notice_version=row.notice_version,
                    locale=row.locale,
                    source=row.source,
                    sequence=row.sequence,
                    decided_at=row.decided_at,
                    supersedes_id=row.supersedes_id,
                )
                for row in rows
            ],
            row_version=max(1, len(rows) + 1),
        )

    def save(self, ledger: ConsentLedger, expected_version: int | None = None) -> None:
        del expected_version
        for decision in ledger.decisions:
            if self.session.get(ConsentDecisionRow, decision.id) is None:
                self.session.add(
                    ConsentDecisionRow(
                        id=decision.id,
                        subject_id=decision.subject_id,
                        subject_type=decision.subject_type,
                        purpose=decision.purpose.value,
                        decision=decision.value.value,
                        policy_version=decision.policy_version,
                        notice_version=decision.notice_version,
                        locale=decision.locale,
                        source=decision.source,
                        sequence=decision.sequence,
                        decided_at=decision.decided_at,
                        supersedes_id=decision.supersedes_id,
                    )
                )
            self.session.merge(
                ConsentCurrentRow(
                    subject_id=decision.subject_id,
                    subject_type=decision.subject_type,
                    purpose=decision.purpose.value,
                    decision_id=decision.id,
                    sequence=decision.sequence,
                )
            )
        self.session.flush()


class SqlAlchemyBehaviorRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def save_event(self, event: BehaviorEvent, dedup_key: str) -> tuple[UUID, bool]:
        existing = self.session.get(
            EventDeduplicationRow, (event.subject_id, event.event_type.value, dedup_key)
        )
        if existing:
            return existing.event_id, False
        self.session.add(
            BehaviorEventRow(
                id=event.id,
                subject_id=event.subject_id,
                content_id=event.content_id,
                event_type=event.event_type.value,
                occurred_at=event.occurred_at,
                received_at=event.received_at,
                source_surface=event.source_surface,
                recommendation_version=event.recommendation_version,
                attributes=event.attributes,
                consent_decision_id=event.consent_decision_id,
                processing_status="pending",
            )
        )
        self.session.add(
            EventDeduplicationRow(
                subject_id=event.subject_id,
                event_type=event.event_type.value,
                dedup_key=dedup_key,
                event_id=event.id,
                expires_at=None,
            )
        )
        self.session.flush()
        return event.id, True

    def get(self, subject_id: str) -> BehaviorEventStream:
        rows = self.session.scalars(
            select(BehaviorEventRow)
            .where(BehaviorEventRow.subject_id == subject_id)
            .order_by(BehaviorEventRow.received_at)
        ).all()
        return BehaviorEventStream(
            subject_id,
            events=[
                BehaviorEvent(
                    id=row.id,
                    subject_id=row.subject_id,
                    content_id=row.content_id,
                    event_type=BehaviorEventType(row.event_type),
                    occurred_at=row.occurred_at,
                    received_at=row.received_at,
                    source_surface=row.source_surface,
                    recommendation_version=row.recommendation_version,
                    attributes=row.attributes,
                    consent_decision_id=row.consent_decision_id,
                )
                for row in rows
            ],
        )


class SqlAlchemyDataRightsRepository:
    def __init__(self, session: SqlSession) -> None:
        self.session = session

    def get(self, request_id: UUID) -> DataRightsRequest | None:
        row = self.session.get(DataRightsRequestRow, request_id)
        if row is None:
            return None
        steps = self.session.scalars(
            select(DeletionStepRow).where(DeletionStepRow.request_id == request_id)
        ).all()
        return DataRightsRequest(
            id=row.id,
            user_id=row.user_id,
            request_type=DataRightsType(row.request_type),
            idempotency_key=row.idempotency_key,
            status=DataRightsStatus(row.status),
            requested_at=row.requested_at,
            reauthenticated_at=row.reauthenticated_at,
            status_version=row.status_version,
            deletion_steps={
                item.category: DeletionStep(
                    item.category, item.completed_at, item.attempt_count, item.failure_code
                )
                for item in steps
            },
        )

    def save(self, request: DataRightsRequest, expected_version: int | None = None) -> None:
        row = self.session.get(DataRightsRequestRow, request.id)
        if row is None:
            self.session.add(
                DataRightsRequestRow(
                    id=request.id,
                    user_id=request.user_id,
                    request_type=request.request_type.value,
                    idempotency_key=request.idempotency_key,
                    status=request.status.value,
                    requested_at=request.requested_at,
                    reauthenticated_at=request.reauthenticated_at,
                    status_version=request.status_version,
                )
            )
        else:
            expected = expected_version if expected_version is not None else row.status_version
            result = self.session.execute(
                update(DataRightsRequestRow)
                .where(
                    DataRightsRequestRow.id == request.id,
                    DataRightsRequestRow.status_version == expected,
                )
                .values(
                    status=request.status.value,
                    reauthenticated_at=request.reauthenticated_at,
                    status_version=request.status_version,
                )
            )
            if getattr(result, "rowcount", 0) != 1:
                raise conflict("optimistic_conflict", "identity.conflict")
        for step in request.deletion_steps.values():
            self.session.merge(
                DeletionStepRow(
                    request_id=request.id,
                    category=step.category,
                    completed_at=step.completed_at,
                    attempt_count=step.attempt_count,
                    failure_code=step.failure_code,
                )
            )
        self.session.flush()


class SqlAlchemyJobPublisher:
    PRIORITY = {"high": 0, "normal": 100, "low": 200}

    def __init__(self, session: SqlSession) -> None:
        self.repository = SqlAlchemyOutboxRepository(session)

    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID:
        if lane not in self.PRIORITY:
            raise ValueError("unknown outbox lane")
        job = OutboxJob(job_type, dict(payload), lane=lane, priority=self.PRIORITY[lane])
        self.repository.enqueue(job)
        return job.id
