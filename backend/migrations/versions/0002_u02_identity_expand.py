"""Add the U02 identity and personalization schema using expand-only changes."""

import sqlalchemy as sa
from alembic import op

revision = "0002_u02_identity_expand"
down_revision = "0001_u07_platform_expand"
branch_labels = None
depends_on = None

SCHEMA = "u02_identity"


def _user_id(*, primary_key: bool = False) -> sa.Column[sa.Uuid]:
    return sa.Column(
        "user_id",
        sa.Uuid(),
        sa.ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"),
        primary_key=primary_key,
        nullable=False,
    )


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("email_ciphertext", sa.JSON(), nullable=False),
        sa.Column("email_blind_index_version", sa.Integer(), nullable=False),
        sa.Column("email_blind_index", sa.LargeBinary(32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("authorization_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("authorization_version > 0", name="ck_users_auth_version"),
        sa.CheckConstraint("row_version > 0", name="ck_users_row_version"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_users_email_blind",
        "users",
        ["email_blind_index_version", "email_blind_index"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("status <> 'deleted'"),
    )
    op.create_table(
        "credentials",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_id(),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_credentials_active_user",
        "credentials",
        ["user_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("disabled_at IS NULL"),
    )
    op.create_table(
        "oauth_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_id(),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_subject_index", sa.LargeBinary(32), nullable=False),
        sa.Column("verified_email_ciphertext", sa.JSON()),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_oauth_active_subject",
        "oauth_links",
        ["provider", "provider_subject_index"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_table(
        "role_assignments",
        _user_id(primary_key=True),
        sa.Column("role", sa.String(40), primary_key=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_by", sa.Uuid()),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_id(),
        sa.Column("token_hmac", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("authorization_version", sa.Integer(), nullable=False),
        sa.Column("device_label", sa.String(120), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fresh_authenticated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoke_reason", sa.String(100)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_sessions_active_expiry",
        "sessions",
        ["user_id", "absolute_expires_at", "last_seen_at"],
        schema=SCHEMA,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_table(
        "verification_challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_id(),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("token_hmac", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "user_profiles",
        _user_id(primary_key=True),
        sa.Column("locale", sa.String(20), nullable=False, server_default="ko-KR"),
        sa.Column("profile_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        schema=SCHEMA,
    )
    op.create_table(
        "genre_preferences",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.user_profiles.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("genre_id", sa.String(100), primary_key=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.CheckConstraint("state IN ('liked', 'disliked')", name="ck_genre_state"),
        schema=SCHEMA,
    )
    op.create_table(
        "ott_subscriptions",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.user_profiles.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("provider_id", sa.String(100), primary_key=True),
        sa.Column("state", sa.String(30), nullable=False),
        sa.CheckConstraint(
            "state IN ('subscribed', 'not_subscribed')", name="ck_ott_subscription_state"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "watch_items",
        _user_id(primary_key=True),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "ratings",
        _user_id(primary_key=True),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("rated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rating_range"),
        schema=SCHEMA,
    )
    op.create_table(
        "watch_history",
        _user_id(primary_key=True),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("last_watched_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "consent_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_id", sa.String(120), nullable=False),
        sa.Column("subject_type", sa.String(20), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("notice_version", sa.String(80), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_id", sa.Uuid()),
        sa.UniqueConstraint(
            "subject_id", "subject_type", "purpose", "sequence", name="uq_consent_sequence"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "consent_current",
        sa.Column("subject_id", sa.String(120), primary_key=True),
        sa.Column("subject_type", sa.String(20), primary_key=True),
        sa.Column("purpose", sa.String(50), primary_key=True),
        sa.Column(
            "decision_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.consent_decisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "guest_link_authorizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("guest_subject_id", sa.String(120), nullable=False),
        _user_id(),
        sa.Column("event_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "behavior_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_id", sa.String(120), nullable=False),
        sa.Column("content_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_surface", sa.String(80), nullable=False),
        sa.Column("recommendation_version", sa.String(100)),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column(
            "consent_decision_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.consent_decisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="pending"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_behavior_subject_received",
        "behavior_events",
        ["subject_id", "received_at"],
        schema=SCHEMA,
    )
    op.create_table(
        "event_deduplication",
        sa.Column("subject_id", sa.String(120), primary_key=True),
        sa.Column("event_type", sa.String(50), primary_key=True),
        sa.Column("dedup_key", sa.String(200), primary_key=True),
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.behavior_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "personalization_features",
        _user_id(primary_key=True),
        sa.Column("feature_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("consent_version", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "feature_contributions",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.personalization_features.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("consent_decision_id", sa.Uuid(), nullable=False),
        sa.Column("applied_feature_version", sa.Integer(), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "data_rights_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_id(),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reauthenticated_at", sa.DateTime(timezone=True)),
        sa.Column("status_version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint(
            "user_id", "request_type", "idempotency_key", name="uq_data_rights_idem"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "export_artifacts",
        sa.Column(
            "request_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.data_rights_requests.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("encrypted_reference", sa.String(500), nullable=False, unique=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "deletion_steps",
        sa.Column(
            "request_id",
            sa.Uuid(),
            sa.ForeignKey(f"{SCHEMA}.data_rights_requests.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("category", sa.String(50), primary_key=True),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_code", sa.String(100)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_deletion_incomplete",
        "deletion_steps",
        ["request_id", "category"],
        schema=SCHEMA,
        postgresql_where=sa.text("completed_at IS NULL"),
    )
    op.create_table(
        "key_rotation_progress",
        sa.Column("from_version", sa.Integer(), primary_key=True),
        sa.Column("to_version", sa.Integer(), primary_key=True),
        sa.Column("cursor", sa.String(200)),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.add_column(
        "outbox_jobs", sa.Column("lane", sa.String(20), nullable=False, server_default="normal")
    )
    op.add_column(
        "outbox_jobs", sa.Column("priority", sa.Integer(), nullable=False, server_default="100")
    )
    op.execute("DROP INDEX IF EXISTS ix_outbox_claim")
    op.create_index(
        "ix_outbox_claim",
        "outbox_jobs",
        ["lane", "status", "available_at", "priority", "job_type"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "Automatic down migration is prohibited; use compatible image rollback and forward recovery"
    )
