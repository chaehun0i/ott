import base64

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ott_feed.identity.adapters.security import EnvelopeCryptography
from ott_feed.identity.domain.errors import IdentityError


@pytest.fixture(scope="module")
def crypto() -> EnvelopeCryptography:
    return EnvelopeCryptography(7, b"kek-v7", b"blind-v7", b"session-v7")


@pytest.mark.pbt
@given(
    record_id=st.text(min_size=1, max_size=64),
    field=st.sampled_from(["email", "oauth_claim"]),
    plaintext=st.text(max_size=512),
)
def test_encryption_round_trip_and_context_binding(
    crypto: EnvelopeCryptography, record_id: str, field: str, plaintext: str
) -> None:
    envelope = crypto.encrypt(record_id, field, plaintext)
    assert crypto.decrypt(record_id, field, envelope) == plaintext
    with pytest.raises(IdentityError):
        crypto.decrypt(record_id + "-different", field, envelope)


@pytest.mark.pbt
@given(value=st.text(min_size=1, max_size=320))
def test_blind_index_is_deterministic_and_domain_separated(
    crypto: EnvelopeCryptography, value: str
) -> None:
    version, email_index = crypto.blind_index("email", value)
    assert version == 7
    assert email_index == crypto.blind_index("email", value)[1]
    assert email_index != crypto.blind_index("oauth", value)[1]


@pytest.mark.pbt
@given(plaintext=st.text(min_size=1, max_size=256))
def test_ciphertext_tampering_never_returns_plaintext(
    crypto: EnvelopeCryptography, plaintext: str
) -> None:
    envelope = crypto.encrypt("record", "email", plaintext)
    encoded = str(envelope["ciphertext"])
    ciphertext = bytearray(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    ciphertext[0] ^= 1
    envelope["ciphertext"] = base64.urlsafe_b64encode(bytes(ciphertext)).decode()
    with pytest.raises(IdentityError, match="ciphertext_integrity_failure"):
        crypto.decrypt("record", "email", envelope)
