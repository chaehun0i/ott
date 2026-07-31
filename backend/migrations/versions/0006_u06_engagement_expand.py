"""U06 engagement and operations expand migration."""

import sqlalchemy as sa
from alembic import op

revision = "0006_u06_engagement_expand"
down_revision = "0005_u05_recommendation_expand"
branch_labels = None
depends_on = None
SCHEMA = "u06_engagement"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "notification_jobs",
        sa.Column("job_id", sa.String(120), primary_key=True),
        sa.Column("deduplication_key", sa.String(64), nullable=False, unique=True),
        sa.Column("event_id", sa.String(120), nullable=False),
        sa.Column("member_ref", sa.String(120), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fencing_token", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(100)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.CheckConstraint("expires_at > available_at", name="ck_u06_job_lifetime"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u06_job_claim",
        "notification_jobs",
        ["channel", "status", "available_at", "job_id"],
        schema=SCHEMA,
    )
    op.create_table(
        "override_operations",
        sa.Column("operation_id", sa.String(120), primary_key=True),
        sa.Column("content_id", sa.String(120), nullable=False),
        sa.Column("actor_ref", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("expected_version", sa.Integer(), nullable=False),
        sa.Column("patch", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("receipt", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("actor_ref", "idempotency_key", name="uq_u06_override_idempotency"),
        schema=SCHEMA,
    )
    op.create_table(
        "audit_events",
        sa.Column("audit_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(120), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_ref", sa.String(120), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("canonical_event", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("key_id", sa.String(80), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u06_audit_time", "audit_events", ["occurred_at", "audit_id"], schema=SCHEMA
    )
    op.create_table(
        "incidents",
        sa.Column("incident_id", sa.String(120), primary_key=True),
        sa.Column("correlation_key", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("occurrences", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(120)),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.execute(
        f"CREATE UNIQUE INDEX uq_u06_incident_open_correlation ON {SCHEMA}.incidents "
        "(correlation_key) WHERE state <> 'resolved'"
    )
    op.create_table(
        "retention_checkpoints",
        sa.Column("retention_class", sa.String(40), primary_key=True),
        sa.Column("cursor", sa.String(120)),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.execute(
        f"CREATE OR REPLACE FUNCTION {SCHEMA}.deny_audit_mutation() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'audit events are append-only'; END $$"
    )
    op.execute(
        f"CREATE TRIGGER trg_u06_audit_immutable BEFORE UPDATE OR DELETE ON "
        f"{SCHEMA}.audit_events FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.deny_audit_mutation()"
    )


def downgrade() -> None:
    raise RuntimeError("Automatic down migration is prohibited; use forward recovery")
