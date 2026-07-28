"""Registration, credential authentication and explicit OAuth linking use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import denied, invalid
from ott_feed.identity.domain.models import Credential, OAuthLink, Session, User
from ott_feed.identity.domain.policies import normalize_email, require_fresh_auth, validate_password
from ott_feed.identity.ports import OAuthIdentityProvider, PasswordHasher, SecretCryptography


class IdentityRepositoryPort(Protocol):
    def get_user(self, user_id: UUID) -> User | None: ...

    def find_user_by_email_index(self, version: int, index: bytes) -> User | None: ...

    def find_user_by_oauth(self, provider: str, subject_index: bytes) -> User | None: ...

    def save_user(self, user: User, expected_version: int | None = None) -> None: ...


class SessionRepositoryPort(Protocol):
    def save_session(self, session: Session) -> None: ...


class JobPublisherPort(Protocol):
    def enqueue(self, job_type: str, payload: dict[str, object], lane: str) -> UUID: ...


class IdentityWork(Protocol):
    identities: IdentityRepositoryPort
    sessions: SessionRepositoryPort
    jobs: JobPublisherPort

    def __enter__(self) -> IdentityWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class ChallengeStore(Protocol):
    def issue(self, user_id: UUID, purpose: str, expires_at: datetime) -> str: ...

    def consume(self, token: str, purpose: str, at: datetime) -> UUID: ...


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    user_id: UUID
    session_id: UUID
    session_token: str
    authorization_version: int


class AuthenticationService:
    def __init__(
        self,
        uow_factory: Callable[[], IdentityWork],
        hasher: PasswordHasher,
        cryptography: SecretCryptography,
        challenges: ChallengeStore,
        now: Callable[[], datetime],
        hash_policy_version: int = 1,
    ) -> None:
        self.uow_factory = uow_factory
        self.hasher = hasher
        self.cryptography = cryptography
        self.challenges = challenges
        self.now = now
        self.hash_policy_version = hash_policy_version

    def register(self, email: str, password: str) -> UUID:
        normalized = normalize_email(email)
        validate_password(password)
        version, email_index = self.cryptography.blind_index("email", normalized)
        now = self.now()
        with self.uow_factory() as work:
            if work.identities.find_user_by_email_index(version, email_index):
                return UUID(int=0)
            user = User(
                email_ciphertext={},
                email_blind_index_version=version,
                email_blind_index=email_index,
                created_at=now,
                updated_at=now,
            )
            user.email_ciphertext = dict(
                self.cryptography.encrypt(str(user.id), "email", normalized)
            )
            user.add_credential(
                Credential(self.hasher.hash(password), self.hash_policy_version), now
            )
            work.identities.save_user(user)
            challenge = self.challenges.issue(user.id, "verify_email", now + timedelta(hours=24))
            work.jobs.enqueue(
                "identity.email.verify",
                {"userId": str(user.id), "challengeReference": challenge},
                "normal",
            )
            work.commit()
            return user.id

    def verify_email(self, token: str) -> UUID:
        now = self.now()
        user_id = self.challenges.consume(token, "verify_email", now)
        with self.uow_factory() as work:
            user = work.identities.get_user(user_id)
            if user is None:
                raise denied("verification_invalid", "identity.verification_invalid")
            expected = user.row_version
            user.verify_email(now)
            work.identities.save_user(user, expected)
            work.commit()
            return user.id

    def login(self, email: str, password: str, device_label: str) -> AuthenticationResult:
        normalized = normalize_email(email)
        version, email_index = self.cryptography.blind_index("email", normalized)
        now = self.now()
        with self.uow_factory() as work:
            user = work.identities.find_user_by_email_index(version, email_index)
            credential = (
                next((item for item in user.credentials if item.active), None) if user else None
            )
            if (
                user is None
                or credential is None
                or not self.hasher.verify(credential.password_hash, password)
            ):
                raise denied("authentication_failed", "identity.authentication_failed")
            user.assert_active()
            if self.hasher.needs_rehash(credential.password_hash):
                expected = user.row_version
                credential.replace(self.hasher.hash(password), self.hash_policy_version, now)
                user.row_version += 1
                user.updated_at = now
                work.identities.save_user(user, expected)
            result = self._new_session(user, device_label, now, work)
            work.commit()
            return result

    def request_password_reset(self, email: str) -> None:
        normalized = normalize_email(email)
        version, email_index = self.cryptography.blind_index("email", normalized)
        now = self.now()
        with self.uow_factory() as work:
            user = work.identities.find_user_by_email_index(version, email_index)
            if user is not None:
                reference = self.challenges.issue(
                    user.id, "reset_password", now + timedelta(minutes=30)
                )
                work.jobs.enqueue(
                    "identity.email.password-reset",
                    {"userId": str(user.id), "challengeReference": reference},
                    "normal",
                )
            work.commit()

    def reset_password(self, token: str, new_password: str) -> UUID:
        validate_password(new_password)
        now = self.now()
        user_id = self.challenges.consume(token, "reset_password", now)
        with self.uow_factory() as work:
            user = work.identities.get_user(user_id)
            if user is None:
                raise denied("reset_invalid", "identity.reset_invalid")
            user.assert_active()
            expected = user.row_version
            credential = next((item for item in user.credentials if item.active), None)
            if credential is None:
                user.add_credential(
                    Credential(self.hasher.hash(new_password), self.hash_policy_version), now
                )
            else:
                credential.replace(self.hasher.hash(new_password), self.hash_policy_version, now)
                user.row_version += 1
                user.updated_at = now
                user.authorization_version += 1
            work.identities.save_user(user, expected)
            work.sessions.revoke_all(user.id, "password_reset", now)  # type: ignore[attr-defined]
            work.commit()
            return user.id

    def oauth_login(
        self,
        provider: OAuthIdentityProvider,
        code: str,
        expected_nonce: str,
        device_label: str,
    ) -> AuthenticationResult:
        claims = provider.exchange(code, expected_nonce)
        subject = str(claims.get("sub", ""))
        if not subject or claims.get("email_verified") is not True:
            raise denied("oauth_claim_invalid", "identity.oauth_failed")
        _, subject_index = self.cryptography.blind_index("oauth:google", subject)
        now = self.now()
        with self.uow_factory() as work:
            user = work.identities.find_user_by_oauth("google", subject_index)
            if user is None:
                raise denied("oauth_link_required", "identity.oauth_link_required")
            user.assert_active()
            result = self._new_session(user, device_label, now, work)
            work.commit()
            return result

    def link_google(
        self,
        user_id: UUID,
        session: Session,
        claims: Mapping[str, object],
    ) -> None:
        now = self.now()
        require_fresh_auth(session, now)
        subject = str(claims.get("sub", ""))
        email = str(claims.get("email", ""))
        if not subject or claims.get("email_verified") is not True:
            raise invalid("oauth_claim_invalid", "identity.oauth_failed")
        _, subject_index = self.cryptography.blind_index("oauth:google", subject)
        with self.uow_factory() as work:
            if work.identities.find_user_by_oauth("google", subject_index):
                raise denied("oauth_subject_in_use", "identity.oauth_link_conflict")
            user = work.identities.get_user(user_id)
            if user is None or session.user_id != user.id:
                raise denied()
            expected = user.row_version
            encrypted_email = (
                dict(self.cryptography.encrypt(str(user.id), "oauth_claim", normalize_email(email)))
                if email
                else None
            )
            user.link_oauth(OAuthLink("google", subject_index, encrypted_email), now)
            work.identities.save_user(user, expected)
            work.commit()

    def unlink_google(self, user_id: UUID, session: Session, link_id: UUID) -> None:
        now = self.now()
        require_fresh_auth(session, now)
        with self.uow_factory() as work:
            user = work.identities.get_user(user_id)
            if user is None or session.user_id != user.id:
                raise denied()
            expected = user.row_version
            user.unlink_oauth(link_id, now)
            work.identities.save_user(user, expected)
            work.commit()

    def _new_session(
        self, user: User, device_label: str, now: datetime, work: IdentityWork
    ) -> AuthenticationResult:
        token, token_hmac = self.cryptography.session_token()
        session = Session(
            user_id=user.id,
            token_hmac=token_hmac,
            authorization_version=user.authorization_version,
            device_label=device_label[:120],
            issued_at=now,
            last_seen_at=now,
            absolute_expires_at=now + timedelta(days=30),
            fresh_authenticated_at=now,
        )
        work.sessions.save_session(session)
        return AuthenticationResult(user.id, session.id, token, user.authorization_version)
