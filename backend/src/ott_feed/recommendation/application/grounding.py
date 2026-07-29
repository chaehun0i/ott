"""Claim validation and safe localized template replacement."""

from ott_feed.recommendation.application.validation import claim_passes
from ott_feed.recommendation.domain.models import (
    AtomicClaim,
    Evidence,
    Locale,
    RankedCandidate,
    SafeRecommendationItem,
)


def assemble_safe_item(
    ranked: RankedCandidate,
    evidence: Evidence,
    claims: tuple[AtomicClaim, ...],
    locale: Locale,
) -> SafeRecommendationItem:
    passed = {claim.field_path: claim.text for claim in claims if claim_passes(claim, evidence)}
    title = evidence.fields["title"]
    default_summary = evidence.fields.get("synopsis", title)
    default_reason = (
        f"{evidence.fields.get('genres', '')} 장르와 요청 조건에 맞아요."
        if locale is Locale.KO
        else f"Matches your request with {evidence.fields.get('genres', '')}."
    )
    return SafeRecommendationItem(
        evidence.content_id,
        title,
        passed.get("synopsis", default_summary),
        passed.get("reason", default_reason),
        ranked.proof.total,
        evidence.metadata_version,
    )
