"""U02 aggregates and state machines described by BR-U02-001 through BR-U02-051."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from ott_feed.identity.domain.errors import conflict, denied, invalid


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserStatus(StrEnum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETION_PENDING = "deletion_pending"
    DELETED = "deleted"


class Role(StrEnum):
    MEMBER = "member"
    CONTENT_OPERATOR = "content_operator"
    SYSTEM_ADMINISTRATOR = "system_administrator"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.MEMBER: frozenset(
        {
            "profile:own",
            "library:own",
            "session:own",
            "consent:own",
            "data_rights:own",
        }
    ),
    Role.CONTENT_OPERATOR: frozenset({"content:operate"}),
    Role.SYSTEM_ADMINISTRATOR: frozenset({"role:admin", "security:audit"}),
}


@dataclass(slots=True)
class Credential:
    password_hash: str
    policy_version: int
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    changed_at: datetime = field(default_factory=utc_now)
    disabled_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.disabled_at is None

    def replace(self, password_hash: str, policy_version: int, at: datetime) -> None:
        if not self.active:
            raise denied("credential_disabled", "identity.authentication_failed")
        self.password_hash = password_hash
        self.policy_version = policy_version
        self.changed_at = at


@dataclass(slots=True)
class OAuthLink:
    provider: str
    provider_subject_index: bytes
    verified_email_ciphertext: dict[str, object] | None
    id: UUID = field(default_factory=uuid4)
    linked_at: datetime = field(default_factory=utc_now)
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None


@dataclass(slots=True)
class User:
    email_ciphertext: dict[str, object]
    email_blind_index_version: int
    email_blind_index: bytes
    id: UUID = field(default_factory=uuid4)
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    email_verified_at: datetime | None = None
    credentials: list[Credential] = field(default_factory=list)
    oauth_links: list[OAuthLink] = field(default_factory=list)
    roles: set[Role] = field(default_factory=set)
    authorization_version: int = 1
    row_version: int = 1
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def verify_email(self, at: datetime) -> None:
        if self.status != UserStatus.PENDING_VERIFICATION:
            raise conflict("email_not_pending", "identity.verification_invalid")
        self.email_verified_at = at
        self.status = UserStatus.ACTIVE
        self.roles.add(Role.MEMBER)
        self._changed(at, authorization=True)

    def add_credential(self, credential: Credential, at: datetime) -> None:
        if any(item.active for item in self.credentials):
            raise conflict("active_credential_exists", "identity.credential_exists")
        self.credentials.append(credential)
        self._changed(at, authorization=True)

    def link_oauth(self, link: OAuthLink, at: datetime) -> None:
        if any(item.active and item.provider == link.provider for item in self.oauth_links):
            raise conflict("oauth_provider_already_linked", "identity.oauth_link_exists")
        self.oauth_links.append(link)
        self._changed(at, authorization=True)

    def unlink_oauth(self, link_id: UUID, at: datetime) -> None:
        link = next((item for item in self.oauth_links if item.id == link_id and item.active), None)
        if link is None:
            raise invalid("oauth_link_not_found", "identity.oauth_link_not_found")
        remaining = sum(item.active and item.id != link_id for item in self.oauth_links)
        usable_password = any(item.active for item in self.credentials)
        if not usable_password and remaining == 0:
            raise conflict("last_login_method", "identity.last_login_method")
        link.revoked_at = at
        self._changed(at, authorization=True)

    def grant_role(self, role: Role, at: datetime) -> None:
        if role not in self.roles:
            self.roles.add(role)
            self._changed(at, authorization=True)

    def revoke_role(self, role: Role, at: datetime) -> None:
        if role == Role.MEMBER and self.status == UserStatus.ACTIVE:
            raise conflict("member_role_required", "identity.member_role_required")
        if role in self.roles:
            self.roles.remove(role)
            self._changed(at, authorization=True)

    def begin_deletion(self, at: datetime) -> None:
        if self.status == UserStatus.DELETED:
            return
        self.status = UserStatus.DELETION_PENDING
        self._changed(at, authorization=True)

    def complete_deletion(self, at: datetime) -> None:
        if self.status != UserStatus.DELETION_PENDING:
            raise conflict("deletion_not_pending", "identity.deletion_not_pending")
        self.status = UserStatus.DELETED
        self._changed(at, authorization=True)

    def assert_active(self) -> None:
        if self.status != UserStatus.ACTIVE:
            raise denied("account_unavailable", "identity.authentication_failed")

    def permissions(self) -> frozenset[str]:
        return frozenset().union(*(ROLE_PERMISSIONS[role] for role in self.roles))

    def _changed(self, at: datetime, *, authorization: bool = False) -> None:
        self.row_version += 1
        self.updated_at = at
        if authorization:
            self.authorization_version += 1


@dataclass(slots=True)
class Session:
    user_id: UUID
    token_hmac: bytes
    authorization_version: int
    device_label: str
    id: UUID = field(default_factory=uuid4)
    issued_at: datetime = field(default_factory=utc_now)
    last_seen_at: datetime = field(default_factory=utc_now)
    absolute_expires_at: datetime = field(default_factory=lambda: utc_now() + timedelta(days=30))
    fresh_authenticated_at: datetime = field(default_factory=utc_now)
    revoked_at: datetime | None = None
    revoke_reason: str | None = None

    def is_active(self, at: datetime, inactivity: timedelta) -> bool:
        return (
            self.revoked_at is None
            and at < self.absolute_expires_at
            and at - self.last_seen_at < inactivity
        )

    def assert_authorized(
        self, at: datetime, inactivity: timedelta, authorization_version: int
    ) -> None:
        invalid_session = not self.is_active(at, inactivity)
        stale_authorization = self.authorization_version != authorization_version
        if invalid_session or stale_authorization:
            raise denied("session_invalid", "identity.session_expired")

    def require_fresh(self, at: datetime, window: timedelta) -> None:
        if at - self.fresh_authenticated_at > window:
            raise denied("fresh_auth_required", "identity.fresh_auth_required")

    def touch(self, at: datetime) -> None:
        if self.revoked_at is not None:
            raise denied("session_revoked", "identity.session_expired")
        self.last_seen_at = max(self.last_seen_at, at)

    def revoke(self, reason: str, at: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = at
            self.revoke_reason = reason


class GenrePreferenceState(StrEnum):
    LIKED = "liked"
    DISLIKED = "disliked"


class OttSubscriptionState(StrEnum):
    SUBSCRIBED = "subscribed"
    NOT_SUBSCRIBED = "not_subscribed"
    UNSPECIFIED = "unspecified"


@dataclass(slots=True)
class UserProfile:
    user_id: UUID
    locale: str = "ko-KR"
    genres: dict[str, GenrePreferenceState] = field(default_factory=dict)
    ott_subscriptions: dict[str, OttSubscriptionState] = field(default_factory=dict)
    profile_version: int = 1
    row_version: int = 1

    def set_genre(self, genre_id: str, state: GenrePreferenceState | None) -> None:
        if state is None:
            self.genres.pop(genre_id, None)
        else:
            self.genres[genre_id] = state
        self._changed()

    def set_ott(self, provider_id: str, state: OttSubscriptionState) -> None:
        if state == OttSubscriptionState.UNSPECIFIED:
            self.ott_subscriptions.pop(provider_id, None)
        else:
            self.ott_subscriptions[provider_id] = state
        self._changed()

    def _changed(self) -> None:
        self.profile_version += 1
        self.row_version += 1


@dataclass(frozen=True, slots=True)
class WatchHistoryEntry:
    completed: bool
    last_watched_at: datetime


@dataclass(slots=True)
class UserLibrary:
    user_id: UUID
    saved: dict[str, datetime] = field(default_factory=dict)
    ratings: dict[str, int] = field(default_factory=dict)
    history: dict[str, WatchHistoryEntry] = field(default_factory=dict)
    row_version: int = 1

    def save(self, content_id: str, at: datetime) -> bool:
        if content_id in self.saved:
            return False
        self.saved[content_id] = at
        self.row_version += 1
        return True

    def unsave(self, content_id: str) -> bool:
        removed = self.saved.pop(content_id, None) is not None
        if removed:
            self.row_version += 1
        return removed

    def rate(self, content_id: str, rating: int) -> None:
        if rating < 1 or rating > 5:
            raise invalid("rating_out_of_range", "identity.rating_invalid")
        self.ratings[content_id] = rating
        self.row_version += 1

    def unrate(self, content_id: str) -> bool:
        removed = self.ratings.pop(content_id, None) is not None
        if removed:
            self.row_version += 1
        return removed

    def complete_watch(self, content_id: str, at: datetime) -> None:
        current = self.history.get(content_id)
        watched_at = max(current.last_watched_at, at) if current else at
        self.history[content_id] = WatchHistoryEntry(True, watched_at)
        self.row_version += 1


class ConsentPurpose(StrEnum):
    REQUIRED_SERVICE = "required_service"
    PERSONALIZATION = "personalization"


class ConsentValue(StrEnum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class ConsentDecision:
    subject_id: str
    subject_type: str
    purpose: ConsentPurpose
    value: ConsentValue
    policy_version: str
    notice_version: str
    locale: str
    source: str
    sequence: int
    decided_at: datetime
    id: UUID = field(default_factory=uuid4)
    supersedes_id: UUID | None = None


@dataclass(slots=True)
class ConsentLedger:
    subject_id: str
    subject_type: str
    decisions: list[ConsentDecision] = field(default_factory=list)
    row_version: int = 1

    def decide(
        self,
        purpose: ConsentPurpose,
        value: ConsentValue,
        policy_version: str,
        notice_version: str,
        locale: str,
        source: str,
        at: datetime,
    ) -> ConsentDecision:
        if not policy_version or not notice_version:
            raise invalid("consent_version_required", "identity.consent_invalid")
        previous = self.current(purpose)
        decision = ConsentDecision(
            subject_id=self.subject_id,
            subject_type=self.subject_type,
            purpose=purpose,
            value=value,
            policy_version=policy_version,
            notice_version=notice_version,
            locale=locale,
            source=source,
            sequence=len(self.decisions) + 1,
            decided_at=at,
            supersedes_id=previous.id if previous else None,
        )
        self.decisions.append(decision)
        self.row_version += 1
        return decision

    def current(self, purpose: ConsentPurpose) -> ConsentDecision | None:
        return next(
            (decision for decision in reversed(self.decisions) if decision.purpose == purpose), None
        )

    def granted(self, purpose: ConsentPurpose) -> ConsentDecision:
        decision = self.current(purpose)
        if decision is None or decision.value != ConsentValue.GRANTED:
            raise denied("consent_required", "identity.personalization_consent_required")
        return decision


@dataclass(slots=True)
class GuestLinkAuthorization:
    guest_subject_id: str
    user_id: UUID
    event_from: datetime
    event_until: datetime
    policy_version: str
    id: UUID = field(default_factory=uuid4)
    granted_at: datetime = field(default_factory=utc_now)
    consumed_at: datetime | None = None

    def consume(self, at: datetime) -> None:
        if self.consumed_at is not None or at > self.event_until:
            raise conflict("guest_link_invalid", "identity.guest_link_invalid")
        self.consumed_at = at


class BehaviorEventType(StrEnum):
    CONTENT_CLICK = "content_click"
    SAVE = "save"
    UNSAVE = "unsave"
    RATE = "rate"
    UNRATE = "unrate"
    RECOMMENDATION_REFRESH = "recommendation_refresh"
    RECOMMENDATION_DISMISS = "recommendation_dismiss"
    OTT_OUTBOUND = "ott_outbound"
    WATCH_COMPLETE = "watch_complete"


@dataclass(frozen=True, slots=True)
class BehaviorEvent:
    subject_id: str
    content_id: str
    event_type: BehaviorEventType
    occurred_at: datetime
    received_at: datetime
    source_surface: str
    consent_decision_id: UUID
    id: UUID = field(default_factory=uuid4)
    recommendation_version: str | None = None
    attributes: dict[str, str | int | bool] = field(default_factory=dict)
    idempotency_key: str | None = None
    fingerprint: str | None = None


@dataclass(slots=True)
class BehaviorEventStream:
    subject_id: str
    events: list[BehaviorEvent] = field(default_factory=list)
    idempotency: dict[tuple[str, str], UUID] = field(default_factory=dict)
    fingerprints: dict[str, UUID] = field(default_factory=dict)

    def append(self, event: BehaviorEvent) -> tuple[UUID, bool]:
        if event.subject_id != self.subject_id:
            raise denied("event_subject_mismatch", "identity.access_denied")
        if event.idempotency_key:
            key = (event.event_type.value, event.idempotency_key)
            if prior := self.idempotency.get(key):
                return prior, False
            self.idempotency[key] = event.id
        elif event.fingerprint:
            if prior := self.fingerprints.get(event.fingerprint):
                return prior, False
            self.fingerprints[event.fingerprint] = event.id
        self.events.append(event)
        return event.id, True


@dataclass(frozen=True, slots=True)
class FeatureContribution:
    event_id: UUID
    name: str
    value: float
    consent_decision_id: UUID


@dataclass(frozen=True, slots=True)
class FeatureSnapshot:
    request_subject: str
    feature_version: int
    consent_version: int
    generated_at: datetime
    valid_until: datetime
    features: dict[str, str | int | float | bool]


@dataclass(slots=True)
class PersonalizationFeatureSet:
    user_id: UUID
    consent_version: int
    features: dict[str, str | int | float | bool] = field(default_factory=dict)
    contributions: dict[UUID, FeatureContribution] = field(default_factory=dict)
    feature_version: int = 1
    row_version: int = 1

    def apply(self, contribution: FeatureContribution, expected_version: int) -> bool:
        if expected_version != self.feature_version:
            raise conflict("feature_version_conflict", "identity.feature_conflict")
        if contribution.event_id in self.contributions:
            return False
        self.contributions[contribution.event_id] = contribution
        self.features[contribution.name] = contribution.value
        self.feature_version += 1
        self.row_version += 1
        return True

    def replace_explicit(
        self,
        values: dict[str, str | int | float | bool],
        consent_version: int,
    ) -> None:
        self.features = values.copy()
        self.consent_version = consent_version
        self.feature_version += 1
        self.row_version += 1

    def snapshot(
        self,
        request_subject: str,
        current_consent_version: int,
        at: datetime,
        lifetime: timedelta = timedelta(minutes=5),
    ) -> FeatureSnapshot:
        if current_consent_version != self.consent_version:
            raise denied("stale_consent_version", "identity.personalization_unavailable")
        return FeatureSnapshot(
            request_subject,
            self.feature_version,
            self.consent_version,
            at,
            at + lifetime,
            self.features.copy(),
        )


class DataRightsType(StrEnum):
    EXPORT = "export"
    DELETION = "deletion"


class DataRightsStatus(StrEnum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    FAILED_RETRYABLE = "failed_retryable"


DELETION_CATEGORIES = (
    "sessions",
    "credentials",
    "oauth_links",
    "profile",
    "library",
    "behavior_events",
    "features",
    "export_artifacts",
)


@dataclass(slots=True)
class DeletionStep:
    category: str
    completed_at: datetime | None = None
    attempt_count: int = 0
    failure_code: str | None = None

    def start(self) -> None:
        if self.completed_at is None:
            self.attempt_count += 1

    def complete(self, at: datetime) -> None:
        self.completed_at = self.completed_at or at
        self.failure_code = None

    def fail(self, code: str) -> None:
        if self.completed_at is None:
            self.failure_code = code


@dataclass(slots=True)
class DataRightsRequest:
    user_id: UUID
    request_type: DataRightsType
    idempotency_key: str
    id: UUID = field(default_factory=uuid4)
    status: DataRightsStatus = DataRightsStatus.REQUESTED
    requested_at: datetime = field(default_factory=utc_now)
    reauthenticated_at: datetime | None = None
    status_version: int = 1
    deletion_steps: dict[str, DeletionStep] = field(default_factory=dict)

    def authorize(self, reauthenticated_at: datetime) -> None:
        if self.status != DataRightsStatus.REQUESTED:
            raise conflict("request_not_authorizable", "identity.data_rights_conflict")
        self.reauthenticated_at = reauthenticated_at
        self.status = DataRightsStatus.AUTHORIZED
        self.status_version += 1
        if self.request_type == DataRightsType.DELETION:
            self.deletion_steps = {
                category: DeletionStep(category) for category in DELETION_CATEGORIES
            }

    def start(self) -> None:
        if self.status not in {
            DataRightsStatus.AUTHORIZED,
            DataRightsStatus.FAILED_RETRYABLE,
            DataRightsStatus.PARTIALLY_COMPLETED,
        }:
            raise conflict("request_not_startable", "identity.data_rights_conflict")
        self.status = DataRightsStatus.PROCESSING
        self.status_version += 1

    def mark_retryable(self) -> None:
        self.status = DataRightsStatus.FAILED_RETRYABLE
        self.status_version += 1

    def complete(self) -> None:
        if self.request_type == DataRightsType.DELETION and any(
            step.completed_at is None for step in self.deletion_steps.values()
        ):
            self.status = DataRightsStatus.PARTIALLY_COMPLETED
            self.status_version += 1
            return
        self.status = DataRightsStatus.COMPLETED
        self.status_version += 1


@dataclass(slots=True)
class ExportArtifact:
    request_id: UUID
    encrypted_reference: str
    checksum: str
    expires_at: datetime
    created_at: datetime = field(default_factory=utc_now)
    consumed_at: datetime | None = None

    def consume(self, at: datetime) -> None:
        if self.consumed_at is not None:
            raise conflict("export_already_consumed", "identity.export_unavailable")
        if at >= self.expires_at:
            raise denied("export_expired", "identity.export_expired")
        self.consumed_at = at


@dataclass(slots=True)
class KeyRotationProgress:
    from_version: int
    to_version: int
    cursor: str | None = None
    processed_rows: int = 0
    failed_rows: int = 0
    completed_at: datetime | None = None

    def checkpoint(self, cursor: str, processed: int, failed: int = 0) -> None:
        if self.completed_at is not None or processed < 0 or failed < 0:
            raise conflict("rotation_checkpoint_invalid", "identity.rotation_conflict")
        self.cursor = cursor
        self.processed_rows += processed
        self.failed_rows += failed

    def complete(self, at: datetime, old_version_rows: int) -> None:
        if old_version_rows != 0:
            raise conflict("old_key_rows_remain", "identity.rotation_incomplete")
        self.completed_at = at


TypedFeatureValue = str | int | float | bool
SafeStatus = dict[str, Any]
