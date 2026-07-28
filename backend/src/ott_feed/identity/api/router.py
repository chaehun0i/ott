"""Versioned FastAPI routes for identity, preferences, feedback and data rights."""
# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response, status

from ott_feed.identity.adapters.security import CsrfProtector
from ott_feed.identity.api.contracts import (
    ConsentRequest,
    ConsentResponse,
    CsrfResponse,
    DataRightsRequestBody,
    DataRightsResponse,
    FeedbackRequest,
    FeedbackResponse,
    LibraryResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordResetCompleteRequest,
    PasswordResetRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    RatingRequest,
    RegisterRequest,
    TokenRequest,
)
from ott_feed.identity.api.dependencies import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    AuthenticatedIdentity,
    facade_from_request,
    identity_from_request,
)
from ott_feed.identity.domain.models import UserLibrary


def _library_response(library: UserLibrary) -> LibraryResponse:
    return LibraryResponse(
        rowVersion=library.row_version,
        saved=sorted(library.saved),
        ratings=dict(sorted(library.ratings.items())),
        completed=sorted(key for key, value in library.history.items() if value.completed),
    )


def create_identity_router(
    csrf: CsrfProtector,
    *,
    secure_cookies: bool,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

    def require_csrf(
        x_csrf_token: str | None = Header(default=None),
        origin: str | None = Header(default=None),
        csrf_cookie: str | None = Cookie(default=None, alias=CSRF_COOKIE),
    ) -> None:
        csrf.verify(csrf_cookie, x_csrf_token, origin)

    protected = [Depends(require_csrf)]

    @router.get("/csrf", response_model=CsrfResponse)
    def issue_csrf(response: Response) -> CsrfResponse:
        token = csrf.issue()
        response.set_cookie(
            CSRF_COOKIE,
            token,
            secure=secure_cookies,
            httponly=False,
            samesite="lax",
            path="/api/v1/identity",
        )
        return CsrfResponse(csrfToken=token)

    @router.post(
        "/register",
        response_model=MessageResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=protected,
    )
    def register(body: RegisterRequest, request: Request) -> MessageResponse:
        facade_from_request(request).register(body.email, body.password)
        return MessageResponse(status="accepted", messageKey="identity.request_accepted")

    @router.post("/verify-email", response_model=MessageResponse, dependencies=protected)
    def verify_email(body: TokenRequest, request: Request) -> MessageResponse:
        facade_from_request(request).verify_email(body.token)
        return MessageResponse(status="completed", messageKey="identity.request_accepted")

    @router.post("/login", response_model=LoginResponse, dependencies=protected)
    def login(body: LoginRequest, request: Request, response: Response) -> LoginResponse:
        user_id, authorization_version, session_token = facade_from_request(request).login(
            body.email, body.password, body.device_label
        )
        response.set_cookie(
            SESSION_COOKIE,
            session_token,
            secure=secure_cookies,
            httponly=True,
            samesite="lax",
            path="/api/v1/identity",
        )
        return LoginResponse(userId=user_id, authorizationVersion=authorization_version)

    @router.post(
        "/password-reset/request",
        response_model=MessageResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=protected,
    )
    def request_password_reset(body: PasswordResetRequest, request: Request) -> MessageResponse:
        facade_from_request(request).request_password_reset(body.email)
        return MessageResponse(status="accepted", messageKey="identity.request_accepted")

    @router.post("/password-reset/complete", response_model=MessageResponse, dependencies=protected)
    def complete_password_reset(
        body: PasswordResetCompleteRequest, request: Request
    ) -> MessageResponse:
        facade_from_request(request).reset_password(body.token, body.new_password)
        return MessageResponse(status="completed", messageKey="identity.request_accepted")

    @router.post("/logout", response_model=MessageResponse, dependencies=protected)
    def logout(
        response: Response,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> MessageResponse:
        facade_from_request(request).revoke_current(identity)
        response.delete_cookie(SESSION_COOKIE, path="/api/v1/identity")
        return MessageResponse(status="completed", messageKey="identity.request_accepted")

    @router.post("/sessions/rotate", response_model=MessageResponse, dependencies=protected)
    def rotate_session(
        response: Response,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> MessageResponse:
        token = facade_from_request(request).rotate_session(identity)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            secure=secure_cookies,
            httponly=True,
            samesite="lax",
            path="/api/v1/identity",
        )
        return MessageResponse(status="completed", messageKey="identity.request_accepted")

    @router.put("/profile", response_model=ProfileResponse, dependencies=protected)
    def update_profile(
        body: ProfileUpdateRequest,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> ProfileResponse:
        profile = facade_from_request(request).update_profile(identity, body)
        return ProfileResponse(
            profileVersion=profile.profile_version,
            genres={key: value.value for key, value in profile.genres.items()},
            ottSubscriptions={key: value.value for key, value in profile.ott_subscriptions.items()},
            locale=profile.locale,
        )

    def mutate_library(
        operation: str,
        content_id: str,
        request: Request,
        identity: AuthenticatedIdentity,
        rating: int | None = None,
    ) -> LibraryResponse:
        library = facade_from_request(request).update_library(
            identity, operation, content_id, rating
        )
        return _library_response(library)

    @router.post(
        "/library/{content_id}/save", response_model=LibraryResponse, dependencies=protected
    )
    def save_content(
        content_id: str,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> LibraryResponse:
        return mutate_library("save", content_id, request, identity)

    @router.delete(
        "/library/{content_id}/save", response_model=LibraryResponse, dependencies=protected
    )
    def unsave_content(
        content_id: str,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> LibraryResponse:
        return mutate_library("unsave", content_id, request, identity)

    @router.put(
        "/library/{content_id}/rating", response_model=LibraryResponse, dependencies=protected
    )
    def rate_content(
        content_id: str,
        body: RatingRequest,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> LibraryResponse:
        return mutate_library("rate", content_id, request, identity, body.rating)

    @router.delete(
        "/library/{content_id}/rating", response_model=LibraryResponse, dependencies=protected
    )
    def unrate_content(
        content_id: str,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> LibraryResponse:
        return mutate_library("unrate", content_id, request, identity)

    @router.post(
        "/library/{content_id}/watch-complete",
        response_model=LibraryResponse,
        dependencies=protected,
    )
    def complete_watch(
        content_id: str,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> LibraryResponse:
        return mutate_library("watch_complete", content_id, request, identity)

    @router.put(
        "/consent/personalization",
        response_model=ConsentResponse,
        dependencies=protected,
    )
    def decide_consent(
        body: ConsentRequest,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> ConsentResponse:
        decision = facade_from_request(request).decide_consent(identity, body)
        return ConsentResponse(
            decisionId=decision.id,
            consentVersion=decision.sequence,
            value=decision.value.value,
        )

    @router.post(
        "/feedback",
        response_model=FeedbackResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=protected,
    )
    def feedback(
        body: FeedbackRequest,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> FeedbackResponse:
        event_id, created = facade_from_request(request).record_feedback(identity, body)
        return FeedbackResponse(eventId=event_id, created=created)

    def request_data_right(
        request_type: str,
        body: DataRightsRequestBody,
        request: Request,
        identity: AuthenticatedIdentity,
    ) -> DataRightsResponse:
        result = facade_from_request(request).request_data_right(
            identity, request_type, body.idempotency_key
        )
        return DataRightsResponse(
            requestId=result.id,
            status=result.status.value,
            statusVersion=result.status_version,
        )

    @router.post(
        "/data-rights/export",
        response_model=DataRightsResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=protected,
    )
    def request_export(
        body: DataRightsRequestBody,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> DataRightsResponse:
        return request_data_right("export", body, request, identity)

    @router.post(
        "/data-rights/deletion",
        response_model=DataRightsResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=protected,
    )
    def request_deletion(
        body: DataRightsRequestBody,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> DataRightsResponse:
        return request_data_right("deletion", body, request, identity)

    @router.get("/data-rights/{request_id}")
    def data_right_status(
        request_id: UUID,
        request: Request,
        identity: AuthenticatedIdentity = Depends(identity_from_request),
    ) -> dict[str, object]:
        return facade_from_request(request).data_right_status(identity, request_id)

    return router
