import pytest

from ott_feed.ingestion.application.normalization import MetadataNormalizer, normalize_text


def test_bilingual_unicode_and_source_paths_are_canonical() -> None:
    result = MetadataNormalizer().normalize(
        {
            "content_type": " MOVIE ",
            "external_ids": {"imdb": " tt123 ", "empty": "  "},
            "titles": {"ko-KR": "  최신\u3000영화 ", "en-US": " New   Movie "},
            "runtime_minutes": 60,
            "genres": [" Comedy ", "comedy", "드라마"],
        },
        raw_record_id="raw-1",
        normalized_id="normalized-1",
    )
    assert result.content_type == "movie"
    assert result.identifiers == (("imdb", "tt123"),)
    assert result.localized_titles == (("en-US", "New Movie"), ("ko-KR", "최신 영화"))
    assert result.genres == ("comedy", "드라마")
    assert "external_ids.imdb" in result.source_paths
    assert "external_ids.empty" not in result.source_paths


def test_runtime_boundary_and_existing_version_fail_closed() -> None:
    normalizer = MetadataNormalizer("v1")
    result = normalizer.normalize(
        {"runtime_minutes": 0}, raw_record_id="raw", normalized_id="normalized"
    )
    assert result.runtime_minutes is None
    assert normalizer.normalize_existing(result) is result
    with pytest.raises(ValueError, match="another version"):
        MetadataNormalizer("v2").normalize_existing(result)


def test_text_normalization_is_idempotent() -> None:
    once = normalize_text("  Ａ   B  ")
    assert normalize_text(once) == once == "A B"
