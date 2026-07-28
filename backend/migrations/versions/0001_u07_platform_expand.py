"""Initial U07 expand-only schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001_u07_platform_expand"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_records",
        sa.Column("scope", sa.String(100), primary_key=True),
        sa.Column("key", sa.String(200), primary_key=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
    )
    op.create_table(
        "outbox_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_code", sa.String(100), nullable=True),
        sa.Column("previous_job_id", sa.Uuid(), nullable=True),
    )
    op.create_index("ix_outbox_claim", "outbox_jobs", ["status", "available_at", "job_type"])
    op.create_table(
        "release_artifacts",
        sa.Column("release_id", sa.String(100), primary_key=True),
        sa.Column("git_revision", sa.String(64), nullable=False),
        sa.Column("release_tag", sa.String(100), nullable=False, unique=True),
        sa.Column("image_digest", sa.String(100), nullable=False, unique=True),
        sa.Column("contract_major", sa.Integer(), nullable=False),
        sa.Column("contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("migration_compatible", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "deployment_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("release_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("previous_digest", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "backup_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("object_key", sa.String(500), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("encrypted", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(100), nullable=True),
    )
    op.create_table(
        "restore_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("backup_id", sa.Uuid(), nullable=False),
        sa.Column("previous_attempt_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("integrity_ok", sa.Boolean(), nullable=False),
        sa.Column("smoke_ok", sa.Boolean(), nullable=False),
        sa.Column("failure_code", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    raise RuntimeError(
        "Automatic down migration is prohibited; use version rollback and recovery runbook"
    )
