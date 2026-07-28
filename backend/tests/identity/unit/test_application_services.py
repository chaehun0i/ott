from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Self
from uuid import UUID, uuid4

import pytest

from ott_feed.identity.adapters.export_storage import (
    EncryptedExportStorage,
    InMemoryPrivateObjectClient,
)
from ott_feed.identity.adapters.security import EnvelopeCryptography
from ott_feed.identity.application.authentication import AuthenticationService
from ott_feed.identity.application.authorization import AuthorizationService
from ott_feed.identity.application.consent import ConsentService
from ott_feed.identity.application.data_rights import (
    DataRightsService,
    DeletionWorker,
    ExportWorker,
)
from ott_feed.identity.application.features import FeatureService
from ott_feed.identity.application.feedback import FeedbackService
from ott_feed.identity.application.library import LibraryService
from ott_feed.identity.application.profile import ProfileService
from ott_feed.identity.application.sessions import SessionService
from ott_feed.identity.domain.errors import IdentityError
from ott_feed.identity.domain.models import (
    BehaviorEvent,
    BehaviorEventType,
    ConsentLedger,
    ConsentValue,
    DataRightsRequest,
    DataRightsStatus,
    FeatureContribution,
    GenrePreferenceState,
    OttSubscriptionState,
    PersonalizationFeatureSet,
    Role,
    Session,
    User,
    UserLibrary,
    UserProfile,
    UserStatus,
)

NOW = datetime(2026, 7, 27, tzinfo=UTC)


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hash:{password}"

    def verify(self, envelope: str, password: str) -> bool:
        return envelope == f"hash:{password}"

    def needs_rehash(self, envelope: str) -> bool:
        return envelope.startswith("old:")


class FakeChallenges:
    def __init__(self) -> None:
        self.tokens: dict[str, tuple[UUID, str, datetime]] = {}

    def issue(self, user_id: UUID, purpose: str, expires_at: datetime) -> str:
        token = f"challenge-{uuid4()}"
        self.tokens[token] = (user_id, purpose, expires_at)
        return token

    def consume(self, token: str, purpose: str, at: datetime) -> UUID:
        try:
            user_id, stored_purpose, expires = self.tokens.pop(token)
        except KeyError as exc:
            raise IdentityError("challenge_invalid", "identity.request_invalid") from exc
        if purpose != stored_purpose or at >= expires:
            raise IdentityError("challenge_invalid", "identity.request_invalid")
        return user_id


class IdentityRepo:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    def get_user(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    def find_user_by_email_index(self, version: int, index: bytes) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.email_blind_index_version == version and user.email_blind_index == index
            ),
            None,
        )

    def find_user_by_oauth(self, provider: str, subject_index: bytes) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if any(
                    link.provider == provider
                    and link.provider_subject_index == subject_index
                    and link.active
                    for link in user.oauth_links
                )
            ),
            None,
        )

    def save_user(self, user: User, expected_version: int | None = None) -> None:
        del expected_version
        self.users[user.id] = user


class SessionRepo:
    def __init__(self) -> None:
        self.sessions: dict[UUID, Session] = {}

    def find_by_token_hmac(self, token_hmac: bytes) -> Session | None:
        return next(
            (session for session in self.sessions.values() if session.token_hmac == token_hmac),
            None,
        )

    def get(self, session_id: UUID) -> Session | None:
        return self.sessions.get(session_id)

    def save_session(self, session: Session) -> None:
        self.sessions[session.id] = session

    def revoke_all(self, user_id: UUID, reason: str, at: datetime) -> int:
        selected = [session for session in self.sessions.values() if session.user_id == user_id]
        for session in selected:
            session.revoke(reason, at)
        return len(selected)


class AggregateRepo:
    def __init__(self, factory=None) -> None:
        self.items: dict[object, object] = {}
        self.factory = factory

    def get(self, key):
        if key not in self.items and self.factory is not None:
            self.items[key] = self.factory(key)
        return self.items.get(key)

    def save(self, value, expected_version=None) -> None:
        del expected_version
        key = getattr(value, "user_id", None) or getattr(value, "id", None)
        if isinstance(value, ConsentLedger):
            key = (value.subject_type, value.subject_id)
        elif isinstance(value, DataRightsRequest):
            key = value.id
        self.items[key] = value


class BehaviorRepo:
    def __init__(self) -> None:
        self.by_key: dict[str, UUID] = {}
        self.events: dict[UUID, BehaviorEvent] = {}

    def save_event(self, event: BehaviorEvent, dedup_key: str) -> tuple[UUID, bool]:
        if dedup_key in self.by_key:
            return self.by_key[dedup_key], False
        self.by_key[dedup_key] = event.id
        self.events[event.id] = event
        return event.id, True


class FeatureRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, PersonalizationFeatureSet] = {}

    def get(self, user_id: UUID) -> PersonalizationFeatureSet | None:
        return self.items.get(user_id)

    def replace_explicit(
        self,
        user_id: UUID,
        values: dict[str, str | int | float | bool],
        consent_version: int,
        expected_feature_version: int,
    ) -> PersonalizationFeatureSet:
        feature_set = self.items.setdefault(
            user_id, PersonalizationFeatureSet(user_id, consent_version)
        )
        if feature_set.feature_version != expected_feature_version:
            raise IdentityError("feature_version_conflict", "identity.feature_conflict")
        feature_set.replace_explicit(values, consent_version)
        return feature_set

    def apply_contribution(
        self,
        user_id: UUID,
        consent_version: int,
        contribution: FeatureContribution,
        expected_feature_version: int,
    ) -> tuple[PersonalizationFeatureSet, bool]:
        feature_set = self.items.setdefault(
            user_id, PersonalizationFeatureSet(user_id, consent_version)
        )
        return feature_set, feature_set.apply(contribution, expected_feature_version)


class JobRepo:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, dict[str, object], str]] = []

    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID:
        self.jobs.append((job_type, payload, lane))
        return uuid4()


class MemoryWork:
    def __init__(self) -> None:
        self.identities = IdentityRepo()
        self.sessions = SessionRepo()
        self.profiles = AggregateRepo(lambda key: UserProfile(key))
        self.libraries = AggregateRepo(lambda key: UserLibrary(key))
        self.consents = AggregateRepo(lambda key: ConsentLedger(key[1], key[0]))
        self.behavior = BehaviorRepo()
        self.features = FeatureRepo()
        self.data_rights = AggregateRepo()
        self.jobs = JobRepo()
        self.commits = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


class Catalog:
    def content_exists(self, content_id: str) -> bool:
        return content_id != "missing"


def active_user() -> User:
    return User(
        {},
        1,
        b"i" * 32,
        status=UserStatus.ACTIVE,
        roles={Role.MEMBER},
        created_at=NOW,
        updated_at=NOW,
    )


def fresh_session(user: User) -> Session:
    return Session(
        user.id,
        b"s" * 32,
        user.authorization_version,
        "browser",
        issued_at=NOW,
        last_seen_at=NOW,
        absolute_expires_at=NOW + timedelta(days=1),
        fresh_authenticated_at=NOW,
    )


def test_authentication_registration_login_reset_and_oauth_paths() -> None:
    work = MemoryWork()
    crypto = EnvelopeCryptography(1, b"kek", b"blind", b"session")
    challenges = FakeChallenges()
    service = AuthenticationService(lambda: work, FakeHasher(), crypto, challenges, lambda: NOW)

    user_id = service.register("member@example.test", "correct horse battery staple")
    assert service.register("MEMBER@example.test", "correct horse battery staple") == UUID(int=0)
    verification = next(
        token for token, value in challenges.tokens.items() if value[1] == "verify_email"
    )
    assert service.verify_email(verification) == user_id
    with pytest.raises(IdentityError, match="authentication_failed"):
        service.login("member@example.test", "wrong password value", "browser")
    login = service.login("member@example.test", "correct horse battery staple", "browser")
    assert login.user_id == user_id
    assert login.session_token

    service.request_password_reset("unknown@example.test")
    service.request_password_reset("member@example.test")
    reset = next(
        token for token, value in challenges.tokens.items() if value[1] == "reset_password"
    )
    assert service.reset_password(reset, "new correct horse battery") == user_id
    assert all(session.revoked_at == NOW for session in work.sessions.sessions.values())

    with pytest.raises(IdentityError, match="oauth_link_required"):
        service.oauth_login(
            type(
                "Provider",
                (),
                {"exchange": lambda self, code, nonce: {"sub": "new", "email_verified": True}},
            )(),
            "code",
            "nonce",
            "browser",
        )
    user = work.identities.get_user(user_id)
    assert user is not None
    session = fresh_session(user)
    service.link_google(
        user.id,
        session,
        {"sub": "google-subject", "email": "member@example.test", "email_verified": True},
    )
    provider = type(
        "Provider",
        (),
        {"exchange": lambda self, code, nonce: {"sub": "google-subject", "email_verified": True}},
    )()
    assert service.oauth_login(provider, "code", "nonce", "browser").user_id == user.id
    service.unlink_google(user.id, session, user.oauth_links[0].id)


def test_session_authorization_profile_and_library_services() -> None:
    work = MemoryWork()
    user = active_user()
    work.identities.save_user(user)
    session = fresh_session(user)
    work.sessions.save_session(session)
    crypto = EnvelopeCryptography(1, b"kek", b"blind", b"session")
    token = "known-token"
    session.token_hmac = crypto.session_token_hmac(token)
    session_service = SessionService(lambda: work, crypto, lambda: NOW)

    resolved_user, resolved_session = session_service.resolve(token)
    assert resolved_user.id == user.id
    rotated_token, replacement = session_service.rotate(user, resolved_session)
    assert rotated_token and replacement.id != session.id
    session_service.revoke(user, replacement, replacement.id)
    another = fresh_session(user)
    work.sessions.save_session(another)
    assert session_service.revoke_all(user, another) >= 1

    admin = active_user()
    admin.roles = {Role.SYSTEM_ADMINISTRATOR}
    admin_session = fresh_session(admin)
    target = active_user()
    work.identities.save_user(target)
    authorization = AuthorizationService(lambda: work, lambda: NOW)
    authorization.grant_role(admin, admin_session, target.id, Role.CONTENT_OPERATOR)
    authorization.revoke_role(admin, admin_session, target.id, Role.CONTENT_OPERATOR)

    profile = ProfileService(lambda: work).update(
        user.id,
        {"comedy": GenrePreferenceState.LIKED},
        {"netflix": OttSubscriptionState.SUBSCRIBED},
        "ko-KR",
    )
    assert profile.genres["comedy"] == GenrePreferenceState.LIKED
    library_service = LibraryService(lambda: work, Catalog(), lambda: NOW)
    assert library_service.save(user.id, "content-1").saved
    library_service.save(user.id, "content-1")
    library_service.rate(user.id, "content-1", 5)
    library_service.unrate(user.id, "content-1")
    library_service.complete_watch(user.id, "content-1")
    library_service.unsave(user.id, "content-1")
    with pytest.raises(IdentityError, match="content_not_found"):
        library_service.save(user.id, "missing")


def test_consent_feedback_and_feature_services() -> None:
    work = MemoryWork()
    user = active_user()
    consent_service = ConsentService(lambda: work, lambda: NOW)
    grant = consent_service.decide_personalization(
        user.id, ConsentValue.GRANTED, "p1", "n1", "ko-KR", "settings"
    )
    assert consent_service.current_personalization(user.id).id == grant.id
    consent_service.authorize_guest_link(
        user.id,
        "guest-pseudonym",
        NOW - timedelta(hours=1),
        NOW,
        "p1",
    )
    crypto = EnvelopeCryptography(1, b"kek", b"blind", b"session")
    feedback = FeedbackService(lambda: work, Catalog(), crypto, lambda: NOW)
    event_id, created = feedback.record(
        user.id,
        "content-1",
        BehaviorEventType.SAVE,
        "feed",
        NOW,
        {},
        "event-key",
        "feed-v1",
    )
    duplicate_id, duplicate_created = feedback.record(
        user.id,
        "content-1",
        BehaviorEventType.SAVE,
        "feed",
        NOW,
        {},
        "event-key",
    )
    assert (duplicate_id, duplicate_created) == (event_id, False)
    assert created is True

    feature_service = FeatureService(lambda: work, crypto, lambda: NOW)
    explicit = feature_service.replace_explicit(user.id, {"genre:comedy": 1.0}, 1)
    contribution = FeatureContribution(uuid4(), "behavior:click", 1.0, grant.id)
    implicit, applied = feature_service.apply_implicit(
        user.id, contribution, explicit.feature_version
    )
    assert applied is True
    snapshot = feature_service.snapshot(user.id, "request-1")
    assert snapshot is not None and snapshot.feature_version == implicit.feature_version
    consent_service.decide_personalization(
        user.id, ConsentValue.WITHDRAWN, "p1", "n1", "ko-KR", "settings"
    )
    with pytest.raises(IdentityError, match="consent_required"):
        feature_service.snapshot(user.id, "request-2")


class ExportProvider:
    def export(self, user_id: UUID) -> dict[str, object]:
        return {"user": str(user_id), "profile": {"locale": "ko-KR"}}


class DeletionHandler:
    def __init__(self, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.deleted: set[str] = set()

    def delete(self, user_id: UUID, category: str) -> None:
        del user_id
        if self.fail_once:
            self.fail_once = False
            raise OSError("injected")
        self.deleted.add(category)

    def remaining(self, user_id: UUID, category: str) -> int:
        del user_id
        return int(category not in self.deleted)


def test_data_rights_export_deletion_retry_and_owner_status() -> None:
    work = MemoryWork()
    user = active_user()
    work.identities.save_user(user)
    session = fresh_session(user)
    work.sessions.save_session(session)
    service = DataRightsService(lambda: work, lambda: NOW)

    export_request = service.request_export(user, session, "export-key")
    storage = EncryptedExportStorage(InMemoryPrivateObjectClient(), b"export-key")
    export_worker = ExportWorker(lambda: work, ExportProvider(), storage, lambda: NOW)
    artifact = export_worker.run(export_request.id)
    assert export_worker.download_once(export_request.id, NOW) != b""
    with pytest.raises(IdentityError):
        export_worker.download_once(export_request.id, NOW)

    deletion_user = active_user()
    work.identities.save_user(deletion_user)
    deletion_session = fresh_session(deletion_user)
    work.sessions.save_session(deletion_session)
    deletion_request = service.request_deletion(deletion_user, deletion_session, "deletion-key")
    handler = DeletionHandler(fail_once=True)
    worker = DeletionWorker(lambda: work, handler, lambda: NOW)
    assert worker.run(deletion_request.id) == DataRightsStatus.PARTIALLY_COMPLETED
    assert worker.run(deletion_request.id) == DataRightsStatus.COMPLETED
    assert service.status(deletion_request.id, deletion_user.id)["status"] == "completed"
    with pytest.raises(IdentityError, match="access_denied"):
        service.status(deletion_request.id, uuid4())
    assert artifact.consumed_at == NOW
