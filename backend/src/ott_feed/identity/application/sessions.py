"""Opaque-session lookup, rotation and revocation use cases."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import denied
from ott_feed.identity.domain.models import Session, User
from ott_feed.identity.ports import SecretCryptography


class SessionWork(Protocol):
    identities: object
    sessions: object

    def __enter__(self) -> SessionWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class SessionService:
    def __init__(
        self,
        uow_factory: Callable[[], SessionWork],
        cryptography: SecretCryptography,
        now: Callable[[], datetime],
        inactivity: timedelta = timedelta(minutes=30),
    ) -> None:
        self.uow_factory = uow_factory
        self.cryptography = cryptography
        self.now = now
        self.inactivity = inactivity

    def resolve(self, token: str) -> tuple[User, Session]:
        token_hmac = self.cryptography.session_token_hmac(token)
        with self.uow_factory() as work:
            session = work.sessions.find_by_token_hmac(token_hmac)  # type: ignore[attr-defined]
            user = work.identities.get_user(session.user_id) if session else None  # type: ignore[attr-defined]
            if session is None or user is None:
                raise denied("session_invalid", "identity.session_expired")
            user.assert_active()
            session.assert_authorized(self.now(), self.inactivity, user.authorization_version)
            session.touch(self.now())
            work.sessions.save_session(session)  # type: ignore[attr-defined]
            work.commit()
            return user, session

    def revoke(self, actor: User, session: Session, target_session_id: UUID) -> None:
        if actor.id != session.user_id:
            raise denied()
        with self.uow_factory() as work:
            target = work.sessions.get(target_session_id)  # type: ignore[attr-defined]
            if target is None or target.user_id != actor.id:
                raise denied()
            target.revoke("user_requested", self.now())
            work.sessions.save_session(target)  # type: ignore[attr-defined]
            work.commit()

    def revoke_all(self, actor: User, session: Session) -> int:
        if actor.id != session.user_id:
            raise denied()
        with self.uow_factory() as work:
            count = work.sessions.revoke_all(actor.id, "user_requested_all", self.now())  # type: ignore[attr-defined]
            work.commit()
            return int(count)

    def rotate(self, user: User, session: Session) -> tuple[str, Session]:
        now = self.now()
        session.assert_authorized(now, self.inactivity, user.authorization_version)
        token, token_hmac = self.cryptography.session_token()
        replacement = Session(
            user_id=user.id,
            token_hmac=token_hmac,
            authorization_version=user.authorization_version,
            device_label=session.device_label,
            issued_at=now,
            last_seen_at=now,
            absolute_expires_at=session.absolute_expires_at,
            fresh_authenticated_at=now,
        )
        with self.uow_factory() as work:
            session.revoke("rotated", now)
            work.sessions.save_session(session)  # type: ignore[attr-defined]
            work.sessions.save_session(replacement)  # type: ignore[attr-defined]
            work.commit()
        return token, replacement
