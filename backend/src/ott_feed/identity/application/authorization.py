"""Current-role authorization and administrative role transitions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ott_feed.identity.domain.errors import denied
from ott_feed.identity.domain.models import Role, Session, User
from ott_feed.identity.domain.policies import (
    authorize_session,
    may_administer_role,
    require_fresh_auth,
)


class AuthorizationWork(Protocol):
    identities: object

    def __enter__(self) -> AuthorizationWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class AuthorizationService:
    def __init__(
        self, uow_factory: Callable[[], AuthorizationWork], now: Callable[[], datetime]
    ) -> None:
        self.uow_factory = uow_factory
        self.now = now

    def require(self, user: User, session: Session, permission: str) -> None:
        authorize_session(session, user, permission, self.now())

    def grant_role(self, actor: User, session: Session, target_id: UUID, role: Role) -> None:
        require_fresh_auth(session, self.now())
        with self.uow_factory() as work:
            target = work.identities.get_user(target_id)  # type: ignore[attr-defined]
            if target is None:
                raise denied()
            may_administer_role(actor, target, role)
            expected = target.row_version
            target.grant_role(role, self.now())
            work.identities.save_user(target, expected)  # type: ignore[attr-defined]
            work.commit()

    def revoke_role(self, actor: User, session: Session, target_id: UUID, role: Role) -> None:
        require_fresh_auth(session, self.now())
        with self.uow_factory() as work:
            target = work.identities.get_user(target_id)  # type: ignore[attr-defined]
            if target is None:
                raise denied()
            may_administer_role(actor, target, role)
            expected = target.row_version
            target.revoke_role(role, self.now())
            work.identities.save_user(target, expected)  # type: ignore[attr-defined]
            work.commit()
