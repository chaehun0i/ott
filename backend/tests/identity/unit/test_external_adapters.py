from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from ott_feed.identity.adapters.email import (
    FakeEmailAdapter,
    MailSinkEmailAdapter,
)
from ott_feed.identity.adapters.google_oauth import GoogleOAuthAdapter
from ott_feed.identity.domain.errors import IdentityError

NOW = datetime(2026, 7, 26, tzinfo=UTC)


def google_adapter(*, transport: httpx.BaseTransport | None = None) -> GoogleOAuthAdapter:
    client = httpx.Client(transport=transport) if transport is not None else None
    return GoogleOAuthAdapter(
        "client-id",
        "client-secret",
        "https://app.example.test/api/v1/identity/oauth/google/callback",
        http_client=client,
        now=lambda: NOW,
    )


def valid_claims() -> dict[str, object]:
    return {
        "iss": "https://accounts.google.com",
        "aud": "client-id",
        "exp": int(NOW.timestamp()) + 300,
        "nonce": "expected-nonce",
        "sub": "provider-subject",
        "email_verified": True,
    }


def test_google_authorization_url_binds_state_nonce_and_exact_redirect() -> None:
    adapter = google_adapter()
    url = httpx.URL(adapter.authorization_url("state-value", "nonce-value"))

    assert url.scheme == "https"
    assert url.host == "accounts.google.com"
    assert url.params["state"] == "state-value"
    assert url.params["nonce"] == "nonce-value"
    assert (
        url.params["redirect_uri"]
        == "https://app.example.test/api/v1/identity/oauth/google/callback"
    )
    adapter.close()


@pytest.mark.parametrize(
    ("replacement", "error_code"),
    [
        ({"iss": "https://attacker.invalid"}, "oauth_claim_invalid"),
        ({"aud": "different-client"}, "oauth_claim_invalid"),
        ({"exp": int(NOW.timestamp()) - 1}, "oauth_claim_invalid"),
        ({"nonce": "replayed-nonce"}, "oauth_claim_invalid"),
        ({"sub": ""}, "oauth_claim_invalid"),
        ({"email_verified": False}, "oauth_claim_invalid"),
    ],
)
def test_google_claim_validation_fails_closed(
    replacement: dict[str, object], error_code: str
) -> None:
    adapter = google_adapter()
    claims = valid_claims() | replacement

    with pytest.raises(IdentityError, match=error_code):
        adapter._validate_claims(claims, "expected-nonce")
    adapter.close()


def test_google_multi_audience_requires_authorized_party() -> None:
    adapter = google_adapter()
    claims = valid_claims() | {"aud": ["client-id", "other-client"]}

    with pytest.raises(IdentityError, match="oauth_claim_invalid"):
        adapter._validate_claims(claims, "expected-nonce")
    adapter._validate_claims(claims | {"azp": "client-id"}, "expected-nonce")
    adapter.close()


def test_google_jwks_fetch_is_bounded_to_two_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def fail(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    monkeypatch.setattr("ott_feed.identity.adapters.google_oauth.time.sleep", lambda _: None)
    adapter = google_adapter(transport=httpx.MockTransport(fail))

    with pytest.raises(IdentityError, match="oauth_jwks_unavailable") as captured:
        adapter._get_jwks()

    assert captured.value.retryable is True
    assert attempts == 2
    adapter.close()


def test_email_fakes_never_record_secret_variables() -> None:
    fake = FakeEmailAdapter()
    fake.send("verify_email", "person@example.test", {"actionUrl": "secret-link"})

    assert fake.sent_templates == ["verify_email"]
    assert "secret-link" not in repr(fake.__dict__)

    sink = MailSinkEmailAdapter()
    sink.send("reset_password", "person@example.test", {"actionUrl": "local-link"})
    assert sink.messages[0].template == "reset_password"
