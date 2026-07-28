"""SQLAlchemy rows for the U02 PostgreSQL-owned schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.platform.adapters.database import Base

SCHEMA = "u02_identity"


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    email_ciphertext: Mapped[dict[str, Any]] = mapped_column(JSON)
    email_blind_index_version: Mapped[int] = mapped_column(Integer)
    email_blind_index: Mapped[bytes] = mapped_column(LargeBinary(32))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authorization_version: Mapped[int] = mapped_column(Integer, default=1)
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CredentialRow(Base):
    __tablename__ = "credentials"
    __table_args__ = (
        Index(
            "uq_credential_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("disabled_at IS NULL"),
        ),
        {"schema": SCHEMA},
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    password_hash: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OAuthLinkRow(Base):
    __tablename__ = "oauth_links"
    __table_args__ = (
        Index(
            "uq_oauth_active_subject",
            "provider",
            "provider_subject_index",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        {"schema": SCHEMA},
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(30))
    provider_subject_index: Mapped[bytes] = mapped_column(LargeBinary(32))
    verified_email_ciphertext: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RoleAssignmentRow(Base):
    __tablename__ = "role_assignments"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(40), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    granted_by: Mapped[UUID | None] = mapped_column(nullable=True)
    reason: Mapped[str] = mapped_column(String(200), default="system")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    token_hmac: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    authorization_version: Mapped[int] = mapped_column(Integer)
    device_label: Mapped[str] = mapped_column(String(120))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fresh_authenticated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(100))


class VerificationChallengeRow(Base):
    __tablename__ = "verification_challenges"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(30))
    token_hmac: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserProfileRow(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(20), default="ko-KR")
    profile_version: Mapped[int] = mapped_column(Integer, default=1)
    row_version: Mapped[int] = mapped_column(Integer, default=1)


class GenrePreferenceRow(Base):
    __tablename__ = "genre_preferences"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.user_profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    state: Mapped[str] = mapped_column(String(20))


class OttSubscriptionRow(Base):
    __tablename__ = "ott_subscriptions"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.user_profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    state: Mapped[str] = mapped_column(String(30))


class WatchItemRow(Base):
    __tablename__ = "watch_items"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RatingRow(Base):
    __tablename__ = "ratings"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer)
    rated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WatchHistoryRow(Base):
    __tablename__ = "watch_history"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    completed: Mapped[bool] = mapped_column(Boolean)
    last_watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConsentDecisionRow(Base):
    __tablename__ = "consent_decisions"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    subject_id: Mapped[str] = mapped_column(String(120), index=True)
    subject_type: Mapped[str] = mapped_column(String(20))
    purpose: Mapped[str] = mapped_column(String(50))
    decision: Mapped[str] = mapped_column(String(20))
    policy_version: Mapped[str] = mapped_column(String(80))
    notice_version: Mapped[str] = mapped_column(String(80))
    locale: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(80))
    sequence: Mapped[int] = mapped_column(Integer)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    supersedes_id: Mapped[UUID | None] = mapped_column(nullable=True)


class ConsentCurrentRow(Base):
    __tablename__ = "consent_current"
    __table_args__ = {"schema": SCHEMA}
    subject_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(50), primary_key=True)
    decision_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.consent_decisions.id", ondelete="CASCADE")
    )
    sequence: Mapped[int] = mapped_column(Integer)


class GuestLinkAuthorizationRow(Base):
    __tablename__ = "guest_link_authorizations"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    guest_subject_id: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    event_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    policy_version: Mapped[str] = mapped_column(String(80))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BehaviorEventRow(Base):
    __tablename__ = "behavior_events"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    subject_id: Mapped[str] = mapped_column(String(120), index=True)
    content_id: Mapped[str] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_surface: Mapped[str] = mapped_column(String(80))
    recommendation_version: Mapped[str | None] = mapped_column(String(100))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON)
    consent_decision_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.consent_decisions.id", ondelete="RESTRICT")
    )
    processing_status: Mapped[str] = mapped_column(String(30), default="pending")


class EventDeduplicationRow(Base):
    __tablename__ = "event_deduplication"
    __table_args__ = {"schema": SCHEMA}
    subject_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    dedup_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.behavior_events.id", ondelete="CASCADE")
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PersonalizationFeatureRow(Base):
    __tablename__ = "personalization_features"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True
    )
    feature_version: Mapped[int] = mapped_column(Integer, default=1)
    consent_version: Mapped[int] = mapped_column(Integer)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeatureContributionRow(Base):
    __tablename__ = "feature_contributions"
    __table_args__ = {"schema": SCHEMA}
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.personalization_features.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    value: Mapped[float] = mapped_column()
    consent_decision_id: Mapped[UUID] = mapped_column(nullable=False)
    applied_feature_version: Mapped[int] = mapped_column(Integer)


class DataRightsRequestRow(Base):
    __tablename__ = "data_rights_requests"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), index=True
    )
    request_type: Mapped[str] = mapped_column(String(20))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reauthenticated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_version: Mapped[int] = mapped_column(Integer, default=1)


class ExportArtifactRow(Base):
    __tablename__ = "export_artifacts"
    __table_args__ = {"schema": SCHEMA}
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.data_rights_requests.id", ondelete="CASCADE"), primary_key=True
    )
    encrypted_reference: Mapped[str] = mapped_column(String(500), unique=True)
    checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeletionStepRow(Base):
    __tablename__ = "deletion_steps"
    __table_args__ = {"schema": SCHEMA}
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.data_rights_requests.id", ondelete="CASCADE"), primary_key=True
    )
    category: Mapped[str] = mapped_column(String(50), primary_key=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(100))


class KeyRotationProgressRow(Base):
    __tablename__ = "key_rotation_progress"
    __table_args__ = {"schema": SCHEMA}
    from_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    to_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    cursor: Mapped[str | None] = mapped_column(String(200))
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
