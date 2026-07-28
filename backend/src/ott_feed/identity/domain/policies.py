"""Pure U02 policy functions shared by application services and tests."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from uuid import UUID

from ott_feed.identity.domain.errors import denied, invalid
from ott_feed.identity.domain.models import (
    ConsentDecision,
    ConsentValue,
    DataRightsRequest,
    FeatureSnapshot,
    PersonalizationFeatureSet,
    Role,
    Session,
    User,
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_FEATURE_PREFIXES = ("genre:", "ott:", "library:", "behavior:")


def normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    if len(normalized) > 320 or not EMAIL_PATTERN.fullmatch(normalized):
        raise invalid("email_invalid", "identity.email_invalid")
    return normalized


def validate_password(value: str) -> str:
    if len(value) < 12 or len(value) > 1024:
        raise invalid("password_policy", "identity.password_policy")
    if value.strip() != value:
        raise invalid("password_whitespace", "identity.password_policy")
    return value


def authorize_session(
    session: Session,
    user: User,
    permission: str,
    at: datetime,
    inactivity: timedelta = timedelta(minutes=30),
) -> None:
    user.assert_active()
    session.assert_authorized(at, inactivity, user.authorization_version)
    if permission not in user.permissions():
        raise denied()


def require_fresh_auth(session: Session, at: datetime) -> None:
    session.require_fresh(at, timedelta(minutes=10))


def may_administer_role(actor: User, target: User, role: Role) -> None:
    actor.assert_active()
    if "role:admin" not in actor.permissions() or actor.id == target.id:
        raise denied()
    if role == Role.SYSTEM_ADMINISTRATOR and Role.SYSTEM_ADMINISTRATOR not in actor.roles:
        raise denied()


def event_fingerprint(
    subject_id: str,
    content_id: str,
    event_type: str,
    occurred_at: datetime,
    attributes: dict[str, str | int | bool],
    window_seconds: int = 10,
) -> str:
    bucket = int(occurred_at.timestamp()) // window_seconds
    normalized_attributes = "&".join(f"{key}={attributes[key]}" for key in sorted(attributes))
    raw = f"{subject_id}|{content_id}|{event_type}|{bucket}|{normalized_attributes}"
    return hashlib.sha256(raw.encode()).hexdigest()


def build_feature_snapshot(
    feature_set: PersonalizationFeatureSet,
    consent: ConsentDecision,
    request_subject: str,
    at: datetime,
) -> FeatureSnapshot:
    if consent.value != ConsentValue.GRANTED:
        raise denied("consent_required", "identity.personalization_consent_required")
    filtered = {
        name: value
        for name, value in feature_set.features.items()
        if name.startswith(ALLOWED_FEATURE_PREFIXES)
    }
    safe_set = PersonalizationFeatureSet(
        user_id=feature_set.user_id,
        consent_version=feature_set.consent_version,
        features=filtered,
        feature_version=feature_set.feature_version,
        row_version=feature_set.row_version,
    )
    return safe_set.snapshot(request_subject, consent.sequence, at)


def deletion_status(request: DataRightsRequest) -> dict[str, object]:
    return {
        "requestId": str(request.id),
        "status": request.status.value,
        "statusVersion": request.status_version,
        "categories": {
            name: "completed" if step.completed_at else "pending"
            for name, step in request.deletion_steps.items()
        },
    }


def request_subject_seed(user_id: UUID, request_id: str) -> bytes:
    return f"{user_id}:{request_id}".encode()
