"""Complete fail-closed candidate and claim validation."""

from collections.abc import Mapping

from ott_feed.recommendation.domain.models import AtomicClaim, Evidence, ValidationState

MANDATORY_PREDICATES = ("approved", "available", "hard_conditions", "evidence")


def candidate_passes(results: Mapping[str, ValidationState]) -> bool:
    return all(results.get(name) is ValidationState.PASSED for name in MANDATORY_PREDICATES)


def claim_passes(claim: AtomicClaim, evidence: Evidence) -> bool:
    return (
        claim.content_id == evidence.content_id
        and claim.metadata_version == evidence.metadata_version
        and claim.field_path in evidence.fields
        and bool(claim.text.strip())
    )
