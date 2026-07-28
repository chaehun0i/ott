from uuid import uuid4

import pytest

from ott_feed.identity.adapters.security import (
    Argon2Policy,
    BoundedArgon2PasswordHasher,
    CsrfProtector,
    EnvelopeCryptography,
)
from ott_feed.identity.domain.errors import IdentityError


@pytest.fixture
def crypto() -> EnvelopeCryptography:
    return EnvelopeCryptography(1, b"kek", b"blind", b"session")


def test_argon2id_hash_verify_and_rehash_contract() -> None:
    hasher = BoundedArgon2PasswordHasher(Argon2Policy(time_cost=1), concurrency=1)
    try:
        envelope = hasher.hash("correct horse battery staple")
        assert envelope.startswith("$argon2id$")
        assert hasher.verify(envelope, "correct horse battery staple")
        assert not hasher.verify(envelope, "incorrect")
        assert not hasher.needs_rehash(envelope)
        assert hasher.needs_rehash("invalid")
    finally:
        hasher.close()


def test_envelope_encryption_binds_record_and_field(crypto: EnvelopeCryptography) -> None:
    envelope = crypto.encrypt("user-1", "email", "member@example.com")
    assert "member@example.com" not in str(envelope)
    assert crypto.decrypt("user-1", "email", envelope) == "member@example.com"
    with pytest.raises(IdentityError, match="ciphertext_integrity_failure"):
        crypto.decrypt("user-2", "email", envelope)


def test_session_token_has_256_bits_and_peppered_lookup(crypto: EnvelopeCryptography) -> None:
    token, token_hmac = crypto.session_token()
    assert len(token_hmac) == 32
    assert token_hmac == crypto.session_token_hmac(token)
    assert token.encode() not in token_hmac


def test_request_pseudonym_is_request_scoped(crypto: EnvelopeCryptography) -> None:
    user_id = uuid4()
    assert crypto.request_pseudonym(user_id, "request-a") != crypto.request_pseudonym(
        user_id, "request-b"
    )


def test_csrf_requires_matching_signed_token_and_allowed_origin() -> None:
    protector = CsrfProtector(b"signing-key", frozenset({"https://example.test"}))
    token = protector.issue()
    protector.verify(token, token, "https://example.test/path")
    with pytest.raises(IdentityError, match="csrf_token_invalid"):
        protector.verify(token, "different", "https://example.test")
    with pytest.raises(IdentityError, match="csrf_origin_invalid"):
        protector.verify(token, token, "https://evil.test")
