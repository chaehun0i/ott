from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Self
from uuid import uuid4

import httpx
import pytest

from ott_feed.identity.adapters.google_oauth import GoogleOAuthAdapter
from ott_feed.identity.adapters.security import EnvelopeCryptography
from ott_feed.identity.application.features import FeatureService
from ott_feed.identity.application.key_rotation import KeyRotationService
from ott_feed.identity.application.sessions import SessionService
from ott_feed.identity.domain.errors import IdentityError
from ott_feed.identity.domain.models import KeyRotationProgress, Role, Session, User, UserStatus
from ott_feed.platform.domain.models import JobStatus, OutboxJob

pytestmark = pytest.mark.integration
NOW = datetime(2026, 7, 27, tzinfo=UTC)


def test_google_timeout_is_bounded_and_does_not_retry_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def timeout(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectTimeout("injected")

    monkeypatch.setattr("ott_feed.identity.adapters.google_oauth.time.sleep", lambda _: None)
    adapter = GoogleOAuthAdapter(
        "client",
        "secret",
        "https://example.test/callback",
        http_client=httpx.Client(transport=httpx.MockTransport(timeout)),
        now=lambda: NOW,
    )
    with pytest.raises(IdentityError, match="oauth_jwks_unavailable"):
        adapter._get_jwks()
    assert attempts == 2
    adapter.close()


class FailingConsentRepository:
    def get(self, key: tuple[str, str]) -> object:
        del key
        raise OSError("injected consent read failure")


class ConsentFailureWork:
    def __init__(self) -> None:
        self.consents = FailingConsentRepository()
        self.features = object()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def commit(self) -> None:
        raise AssertionError("fail-closed path must not commit")


def test_consent_read_failure_never_returns_personalized_snapshot() -> None:
    service = FeatureService(
        lambda: ConsentFailureWork(),
        EnvelopeCryptography(1, b"kek", b"blind", b"session"),
        lambda: NOW,
    )
    with pytest.raises(OSError, match="consent read failure"):
        service.snapshot(uuid4(), "request")


class FailingSessionRepository:
    def find_by_token_hmac(self, token_hmac: bytes) -> None:
        del token_hmac
        return None

    def save_session(self, session: Session) -> None:
        del session
        raise OSError("injected session write failure")


class SessionFailureWork:
    def __init__(self) -> None:
        self.sessions = FailingSessionRepository()
        self.identities = object()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def commit(self) -> None:
        raise AssertionError("failed session write must not commit")


def test_session_rotation_write_failure_returns_no_new_token() -> None:
    user = User(
        {},
        1,
        b"i" * 32,
        status=UserStatus.ACTIVE,
        roles={Role.MEMBER},
        created_at=NOW,
        updated_at=NOW,
    )
    session = Session(
        user.id,
        b"s" * 32,
        user.authorization_version,
        "browser",
        issued_at=NOW,
        last_seen_at=NOW,
        absolute_expires_at=NOW + timedelta(days=1),
        fresh_authenticated_at=NOW,
    )
    service = SessionService(
        lambda: SessionFailureWork(),
        EnvelopeCryptography(1, b"kek", b"blind", b"session"),
        lambda: NOW,
    )
    with pytest.raises(OSError, match="session write failure"):
        service.rotate(user, session)


def test_retry_exhaustion_dead_letters_without_unbounded_backlog_loop() -> None:
    job = OutboxJob("identity.data-rights.deletion", {}, lane="high", max_attempts=3)
    for attempt in range(1, 4):
        job.available_at = NOW
        job.claim("worker", timedelta(seconds=10), NOW)
        job.fail("worker", "InjectedFailure", NOW)
        assert job.attempt_count == attempt
    assert job.status == JobStatus.DEAD_LETTER


class RotationRepository:
    def __init__(self) -> None:
        self.progress: KeyRotationProgress | None = None

    def get(self, from_version: int, to_version: int) -> KeyRotationProgress | None:
        del from_version, to_version
        return self.progress

    def save(self, progress: KeyRotationProgress) -> None:
        self.progress = progress


class RotationStore:
    def __init__(self) -> None:
        self.rows = [(str(index), "email", f"value-{index}") for index in range(501)]
        self.completed: set[str] = set()

    def fetch_batch(
        self, from_version: int, cursor: str | None, limit: int
    ) -> list[tuple[str, str, str]]:
        del from_version
        start = int(cursor) + 1 if cursor else 0
        return self.rows[start : start + limit]

    def reencrypt(self, record_id: str, field: str, plaintext: str, to_version: int) -> None:
        del field, plaintext, to_version
        self.completed.add(record_id)

    def old_version_count(self, version: int) -> int:
        del version
        return len(self.rows) - len(self.completed)


def test_key_rotation_restarts_from_500_row_checkpoint() -> None:
    repository = RotationRepository()
    store = RotationStore()
    service = KeyRotationService(repository, store, lambda: NOW)

    first = service.run_batch(1, 2)
    assert first.cursor == "499"
    assert first.processed_rows == 500
    assert first.completed_at is None
    final = service.run_batch(1, 2)
    assert final.processed_rows == 501
    assert final.completed_at == NOW
