from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from ott_feed.identity.api.dependencies import AuthenticatedIdentity, UnavailableIdentityFacade
from ott_feed.identity.config import IdentitySettings
from ott_feed.identity.domain.models import (
    ConsentDecision,
    ConsentPurpose,
    ConsentValue,
    DataRightsRequest,
    DataRightsType,
    GenrePreferenceState,
    Role,
    Session,
    User,
    UserLibrary,
    UserProfile,
    UserStatus,
)
from ott_feed.main import create_app
from ott_feed.platform.config import Settings


class LoginFacade(UnavailableIdentityFacade):
    def login(self, email: str, password: str, device_label: str) -> tuple[UUID, int, str]:
        assert email == "member@example.test"
        assert password == "correct horse battery staple"
        assert device_label == "contract browser"
        return UUID("d0c77e36-29b4-4ed9-a20b-a8bf1860c9b1"), 4, "opaque-session-token"


class RecordingFacade(LoginFacade):
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 27, tzinfo=UTC)
        self.user = User(
            {},
            1,
            b"i" * 32,
            status=UserStatus.ACTIVE,
            roles={Role.MEMBER},
            created_at=self.now,
            updated_at=self.now,
        )
        self.session = Session(
            self.user.id,
            b"s" * 32,
            self.user.authorization_version,
            "browser",
            issued_at=self.now,
            last_seen_at=self.now,
            absolute_expires_at=self.now + timedelta(days=1),
            fresh_authenticated_at=self.now,
        )
        self.operations: list[str] = []

    def resolve(self, session_token: str) -> AuthenticatedIdentity:
        assert session_token in {"current-token", "rotated-token"}
        return AuthenticatedIdentity(self.user, self.session)

    def rotate_session(self, identity: AuthenticatedIdentity) -> str:
        assert identity.user.id == self.user.id
        self.operations.append("rotate")
        return "rotated-token"

    def update_profile(self, identity: AuthenticatedIdentity, request: object) -> UserProfile:
        self.operations.append("profile")
        return UserProfile(
            identity.user.id,
            genres={"comedy": GenrePreferenceState.LIKED},
            profile_version=2,
            row_version=2,
        )

    def update_library(
        self,
        identity: AuthenticatedIdentity,
        operation: str,
        content_id: str,
        rating: int | None = None,
    ) -> UserLibrary:
        self.operations.append(operation)
        library = UserLibrary(identity.user.id)
        library.save(content_id, self.now)
        if rating is not None:
            library.rate(content_id, rating)
        return library

    def decide_consent(self, identity: AuthenticatedIdentity, request: object) -> ConsentDecision:
        self.operations.append("consent")
        return ConsentDecision(
            str(identity.user.id),
            "user",
            ConsentPurpose.PERSONALIZATION,
            ConsentValue.GRANTED,
            "p1",
            "n1",
            "ko-KR",
            "settings",
            1,
            self.now,
        )

    def record_feedback(
        self, identity: AuthenticatedIdentity, request: object
    ) -> tuple[UUID, bool]:
        self.operations.append("feedback")
        return UUID("39da0d91-c813-4ae9-8248-5f96f34207f7"), True

    def request_data_right(
        self, identity: AuthenticatedIdentity, request_type: str, idempotency_key: str
    ) -> DataRightsRequest:
        self.operations.append(request_type)
        result = DataRightsRequest(identity.user.id, DataRightsType(request_type), idempotency_key)
        result.authorize(self.now)
        return result

    def data_right_status(
        self, identity: AuthenticatedIdentity, request_id: UUID
    ) -> dict[str, object]:
        self.operations.append("status")
        return {"requestId": str(request_id), "status": "authorized", "statusVersion": 2}


def client(facade: UnavailableIdentityFacade | None = None) -> TestClient:
    app = create_app(
        settings=Settings("test", "sqlite+pysqlite:///:memory:", "example.test", b"test-key"),
        identity_facade=facade,
        identity_settings=replace(IdentitySettings.from_environment("local"), environment="test"),
    )
    return TestClient(app, base_url="https://example.test")


def test_login_requires_exact_origin_and_sets_hardened_cookie() -> None:
    with client(LoginFacade()) as api:
        csrf = api.get("/api/v1/identity/csrf").json()["csrfToken"]
        response = api.post(
            "/api/v1/identity/login",
            headers={"origin": "https://example.test", "x-csrf-token": csrf},
            json={
                "email": "member@example.test",
                "password": "correct horse battery staple",
                "deviceLabel": "contract browser",
            },
        )

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "ott_session=" in cookie
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "opaque-session-token" not in response.text


def test_csrf_origin_failure_is_safe_and_localized() -> None:
    with client(LoginFacade()) as api:
        csrf = api.get("/api/v1/identity/csrf").json()["csrfToken"]
        response = api.post(
            "/api/v1/identity/login",
            headers={
                "accept-language": "en",
                "origin": "https://attacker.invalid",
                "x-csrf-token": csrf,
            },
            json={
                "email": "member@example.test",
                "password": "correct horse battery staple",
                "deviceLabel": "contract browser",
            },
        )

    assert response.status_code == 403
    payload = response.json()["error"]
    assert payload["code"] == "csrf_origin_invalid"
    assert payload["messageKey"] == "identity.csrf_invalid"
    assert payload["message"] == "The request could not be verified."


def test_openapi_exposes_versioned_identity_contract_without_secrets() -> None:
    schema = client().app.openapi()

    assert "/api/v1/identity/feedback" in schema["paths"]
    assert "/api/v1/identity/data-rights/deletion" in schema["paths"]
    serialized = str(schema).lower()
    assert "password_hash" not in serialized
    assert "token_hmac" not in serialized
    assert "oauth_subject" not in serialized


def test_authenticated_contracts_cover_rotation_profile_consent_feedback_and_rights() -> None:
    facade = RecordingFacade()
    with client(facade) as api:
        csrf = api.get("/api/v1/identity/csrf").json()["csrfToken"]
        api.cookies.set("ott_session", "current-token")
        headers = {"origin": "https://example.test", "x-csrf-token": csrf}

        assert api.post("/api/v1/identity/sessions/rotate", headers=headers).status_code == 200
        assert (
            api.put(
                "/api/v1/identity/profile",
                headers=headers,
                json={"genres": {"comedy": "liked"}},
            ).status_code
            == 200
        )
        assert (
            api.put(
                "/api/v1/identity/consent/personalization",
                headers=headers,
                json={
                    "value": "granted",
                    "policyVersion": "p1",
                    "noticeVersion": "n1",
                    "locale": "ko-KR",
                },
            ).status_code
            == 200
        )
        assert (
            api.post(
                "/api/v1/identity/feedback",
                headers=headers,
                json={
                    "contentId": "content-1",
                    "eventType": "click",
                    "sourceSurface": "feed",
                    "occurredAt": facade.now.isoformat(),
                    "idempotencyKey": "feedback-key-1",
                },
            ).status_code
            == 202
        )
        export = api.post(
            "/api/v1/identity/data-rights/export",
            headers=headers,
            json={"idempotencyKey": "export-key-1"},
        )
        deletion = api.post(
            "/api/v1/identity/data-rights/deletion",
            headers=headers,
            json={"idempotencyKey": "delete-key-1"},
        )

    assert export.status_code == deletion.status_code == 202
    assert {"rotate", "profile", "consent", "feedback", "export", "deletion"}.issubset(
        facade.operations
    )
