"""Google OAuth/OIDC adapter with callback isolation and bounded JWKS retrieval."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import httpx
from authlib.integrations.httpx_client import OAuth2Client  # type: ignore[import-untyped]
from joserfc import jwt
from joserfc.jwk import KeySet

from ott_feed.identity.domain.errors import denied, unavailable

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
JWKS_ENDPOINT = "https://www.googleapis.com/oauth2/v3/certs"
VALID_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


class GoogleOAuthAdapter:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: httpx.Client | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not client_id or not client_secret or not redirect_uri.startswith("https://"):
            raise ValueError("Google OAuth requires client credentials and an HTTPS redirect URI")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.http = http_client or httpx.Client(
            timeout=httpx.Timeout(10.0, connect=3.0), follow_redirects=False
        )
        self.now = now or (lambda: datetime.now(UTC))
        self._jwks: KeySet | None = None
        self._jwks_expires_at: datetime | None = None
        self._failures = 0
        self._circuit_opened_at: datetime | None = None

    def authorization_url(self, state: str, nonce: str) -> str:
        with OAuth2Client(
            self.client_id,
            self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="openid email",
        ) as client:
            url, _ = client.create_authorization_url(
                AUTHORIZATION_ENDPOINT,
                state=state,
                nonce=nonce,
                prompt="select_account",
            )
        return str(url)

    def exchange(self, code: str, expected_nonce: str) -> Mapping[str, object]:
        if not code or not expected_nonce:
            raise denied("oauth_callback_invalid", "identity.oauth_failed")
        try:
            with OAuth2Client(
                self.client_id,
                self.client_secret,
                redirect_uri=self.redirect_uri,
                timeout=httpx.Timeout(10.0, connect=3.0),
            ) as client:
                token = client.fetch_token(TOKEN_ENDPOINT, code=code)
        except (httpx.HTTPError, OSError, ValueError) as exc:
            raise unavailable("oauth_exchange_failed", "identity.oauth_unavailable") from exc
        id_token = token.get("id_token")
        if not isinstance(id_token, str):
            raise denied("oauth_id_token_missing", "identity.oauth_failed")
        try:
            decoded = jwt.decode(id_token, self._get_jwks(), algorithms=["RS256"])
            claims = dict(decoded.claims)
        except Exception as exc:
            raise denied("oauth_id_token_invalid", "identity.oauth_failed") from exc
        self._validate_claims(claims, expected_nonce)
        return claims

    def _get_jwks(self) -> KeySet:
        now = self.now()
        if self._jwks is not None and self._jwks_expires_at and now < self._jwks_expires_at:
            return self._jwks
        if self._circuit_opened_at and now - self._circuit_opened_at < timedelta(seconds=30):
            raise unavailable("oauth_jwks_circuit_open", "identity.oauth_unavailable")
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = self.http.get(JWKS_ENDPOINT)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("JWKS response is not an object")
                self._jwks = KeySet.import_key_set(cast(Any, payload))
                self._jwks_expires_at = now + timedelta(hours=1)
                self._failures = 0
                self._circuit_opened_at = None
                return self._jwks
            except (httpx.HTTPError, OSError, ValueError) as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.1)
        self._failures += 1
        if self._failures >= 5:
            self._circuit_opened_at = now
        raise unavailable("oauth_jwks_unavailable", "identity.oauth_unavailable") from last_error

    def _validate_claims(self, claims: Mapping[str, object], expected_nonce: str) -> None:
        issuer = str(claims.get("iss", ""))
        audience = claims.get("aud")
        if isinstance(audience, list):
            audiences = {str(item) for item in audience}
        else:
            audiences = {str(audience)}
        expires_at_claim = claims.get("exp")
        if not isinstance(expires_at_claim, (int, str)):
            raise denied("oauth_claim_invalid", "identity.oauth_failed")
        expires_at = int(expires_at_claim)
        authorized_party = claims.get("azp")
        if issuer not in VALID_ISSUERS or self.client_id not in audiences:
            raise denied("oauth_claim_invalid", "identity.oauth_failed")
        if len(audiences) > 1 and authorized_party != self.client_id:
            raise denied("oauth_claim_invalid", "identity.oauth_failed")
        if expires_at <= int(self.now().timestamp()) or claims.get("nonce") != expected_nonce:
            raise denied("oauth_claim_invalid", "identity.oauth_failed")
        if not claims.get("sub") or claims.get("email_verified") is not True:
            raise denied("oauth_claim_invalid", "identity.oauth_failed")

    def close(self) -> None:
        self.http.close()
