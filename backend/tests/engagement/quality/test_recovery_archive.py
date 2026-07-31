import pytest
from cryptography.exceptions import InvalidTag

from ott_feed.engagement.recovery import create_key_archive, restore_key_archive


def test_key_archive_encrypted_signed_round_trip_and_retention() -> None:
    wrapping = b"w" * 32
    archive = create_key_archive({"current": b"c" * 32, "previous": b"p" * 32}, wrapping)
    assert b"current" not in archive and b"previous" not in archive
    restored = restore_key_archive(archive, wrapping)
    assert restored.key_ids == {"current", "previous"}
    assert restored.retention_days == 400


def test_key_archive_wrong_wrapping_key_fails_closed() -> None:
    archive = create_key_archive({"current": b"c" * 32}, b"w" * 32)
    with pytest.raises(InvalidTag):
        restore_key_archive(archive, b"x" * 32)
