"""U03 approved-catalog adapter producing detached U05 values."""

from collections.abc import Mapping

from ott_feed.recommendation.domain.models import ApprovedCandidate


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).casefold() for item in value)


def detach_approved_candidate(value: Mapping[str, object]) -> ApprovedCandidate:
    if value.get("approval_state") != "approved":
        raise ValueError("only approved catalog values are accepted")
    return ApprovedCandidate(
        content_id=str(value["content_id"]),
        metadata_version=str(value["metadata_version"]),
        title=str(value["title"]),
        synopsis=str(value.get("synopsis", "")),
        genres=_strings(value.get("genres")),
        runtime_minutes=int(str(value["runtime_minutes"])),
        region=str(value["region"]).casefold(),
        ott=_strings(value.get("ott")),
        age_rating=int(str(value.get("age_rating", 0))),
        freshness=float(str(value.get("freshness", 0))),
        popularity=float(str(value.get("popularity", 0))),
        franchise=str(value["franchise"]) if value.get("franchise") else None,
    )
