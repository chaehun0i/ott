from datetime import UTC, datetime

from ott_feed.ingestion.application.identity import IdentityResolver
from ott_feed.ingestion.application.merge import MergeEngine
from ott_feed.ingestion.application.normalization import MetadataNormalizer
from ott_feed.ingestion.application.validation import (
    ValidationEngine,
    require_provenance,
    require_title,
)
from ott_feed.ingestion.contracts import ApprovedCatalogCommandMapper
from ott_feed.ingestion.domain.models import ValidationRuleVersion

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def test_us_020_collect_normalize_validate_and_publish_command() -> None:
    normalized = MetadataNormalizer().normalize(
        {
            "content_type": "movie",
            "external_ids": {"imdb": "tt-us020"},
            "titles": {"ko-KR": "통합 테스트 영화"},
            "runtime_minutes": 55,
            "genres": ["comedy"],
        },
        raw_record_id="raw-us020",
        normalized_id="normalized-us020",
    )
    identity = IdentityResolver(("imdb",), {}, lambda: "content-us020").resolve(
        normalized, "resolution-us020"
    )
    assert identity.selected_content_id == "content-us020"
    merged = MergeEngine({"provider": 10}).merge(
        merged_id="merged-us020",
        canonical_content_id=identity.selected_content_id,
        inputs=(("provider", NOW, normalized),),
        computed_at=NOW,
    )
    version = ValidationRuleVersion(
        "rules-v1", ("VAL_SCHEMA_TITLE", "VAL_PROVENANCE"), "u03-v1", "u05-v1", NOW
    )
    _, decision = ValidationEngine(
        {"VAL_SCHEMA_TITLE": require_title, "VAL_PROVENANCE": require_provenance}
    ).evaluate(merged, version, run_id="run-us020", decision_id="decision-us020", evaluated_at=NOW)
    command = ApprovedCatalogCommandMapper().map(decision)
    assert command.merged_id == "merged-us020"
    assert command.publication_key == decision.publication_key
