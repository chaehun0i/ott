"""Framework boundary and dependency contracts for the U02 HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn, Protocol
from uuid import UUID

from fastapi import Request

from ott_feed.identity.api.contracts import (
    ConsentRequest,
    FeedbackRequest,
    ProfileUpdateRequest,
)
from ott_feed.identity.domain.errors import unavailable
from ott_feed.identity.domain.models import (
    BehaviorEventType,
    ConsentDecision,
    ConsentValue,
    DataRightsRequest,
    Session,
    User,
    UserLibrary,
    UserProfile,
)

SESSION_COOKIE = "ott_session"
CSRF_COOKIE = "ott_csrf"
OAUTH_STATE_COOKIE = "ott_oauth_state"
OAUTH_NONCE_COOKIE = "ott_oauth_nonce"


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    user: User
    session: Session


class IdentityFacade(Protocol):
    def register(self, email: str, password: str) -> None: ...

    def verify_email(self, token: str) -> None: ...

    def login(self, email: str, password: str, device_label: str) -> tuple[UUID, int, str]: ...

    def request_password_reset(self, email: str) -> None: ...

    def reset_password(self, token: str, password: str) -> None: ...

    def resolve(self, session_token: str) -> AuthenticatedIdentity: ...

    def revoke_current(self, identity: AuthenticatedIdentity) -> None: ...

    def rotate_session(self, identity: AuthenticatedIdentity) -> str: ...

    def update_profile(
        self, identity: AuthenticatedIdentity, request: ProfileUpdateRequest
    ) -> UserProfile: ...

    def update_library(
        self,
        identity: AuthenticatedIdentity,
        operation: str,
        content_id: str,
        rating: int | None = None,
    ) -> UserLibrary: ...

    def decide_consent(
        self, identity: AuthenticatedIdentity, request: ConsentRequest
    ) -> ConsentDecision: ...

    def record_feedback(
        self, identity: AuthenticatedIdentity, request: FeedbackRequest
    ) -> tuple[UUID, bool]: ...

    def request_data_right(
        self, identity: AuthenticatedIdentity, request_type: str, idempotency_key: str
    ) -> DataRightsRequest: ...

    def data_right_status(
        self, identity: AuthenticatedIdentity, request_id: UUID
    ) -> dict[str, object]: ...


class UnavailableIdentityFacade:
    """Fail-closed placeholder used until a runtime composition is supplied."""

    @staticmethod
    def _raise() -> NoReturn:
        raise unavailable("identity_runtime_unavailable", "identity.try_again")

    def register(self, email: str, password: str) -> None:
        del email, password
        self._raise()

    def verify_email(self, token: str) -> None:
        del token
        self._raise()

    def login(self, email: str, password: str, device_label: str) -> tuple[UUID, int, str]:
        del email, password, device_label
        self._raise()

    def request_password_reset(self, email: str) -> None:
        del email
        self._raise()

    def reset_password(self, token: str, password: str) -> None:
        del token, password
        self._raise()

    def resolve(self, session_token: str) -> AuthenticatedIdentity:
        del session_token
        self._raise()

    def revoke_current(self, identity: AuthenticatedIdentity) -> None:
        del identity
        self._raise()

    def rotate_session(self, identity: AuthenticatedIdentity) -> str:
        del identity
        self._raise()

    def update_profile(
        self, identity: AuthenticatedIdentity, request: ProfileUpdateRequest
    ) -> UserProfile:
        del identity, request
        self._raise()

    def update_library(
        self,
        identity: AuthenticatedIdentity,
        operation: str,
        content_id: str,
        rating: int | None = None,
    ) -> UserLibrary:
        del identity, operation, content_id, rating
        self._raise()

    def decide_consent(
        self, identity: AuthenticatedIdentity, request: ConsentRequest
    ) -> ConsentDecision:
        del identity, request
        self._raise()

    def record_feedback(
        self, identity: AuthenticatedIdentity, request: FeedbackRequest
    ) -> tuple[UUID, bool]:
        del identity, request
        self._raise()

    def request_data_right(
        self, identity: AuthenticatedIdentity, request_type: str, idempotency_key: str
    ) -> DataRightsRequest:
        del identity, request_type, idempotency_key
        self._raise()

    def data_right_status(
        self, identity: AuthenticatedIdentity, request_id: UUID
    ) -> dict[str, object]:
        del identity, request_id
        self._raise()


def facade_from_request(request: Request) -> IdentityFacade:
    return request.app.state.identity_facade  # type: ignore[no-any-return]


def identity_from_request(request: Request) -> AuthenticatedIdentity:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        from ott_feed.identity.domain.errors import denied

        raise denied("session_missing", "identity.session_expired")
    return facade_from_request(request).resolve(token)


__all__ = [
    "AuthenticatedIdentity",
    "BehaviorEventType",
    "ConsentValue",
    "CSRF_COOKIE",
    "facade_from_request",
    "IdentityFacade",
    "identity_from_request",
    "OAUTH_NONCE_COOKIE",
    "OAUTH_STATE_COOKIE",
    "SESSION_COOKIE",
    "UnavailableIdentityFacade",
]
