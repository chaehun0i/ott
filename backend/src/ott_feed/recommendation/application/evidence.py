"""Allowlisted, candidate-local evidence projection."""

from ott_feed.recommendation.domain.models import ApprovedCandidate, Evidence


def build_evidence(candidate: ApprovedCandidate) -> Evidence:
    return Evidence(
        candidate.content_id,
        candidate.metadata_version,
        {
            "title": candidate.title,
            "synopsis": candidate.synopsis,
            "genres": ",".join(candidate.genres),
            "runtime_minutes": str(candidate.runtime_minutes),
            "ott": ",".join(candidate.ott),
            "region": candidate.region,
        },
    )
