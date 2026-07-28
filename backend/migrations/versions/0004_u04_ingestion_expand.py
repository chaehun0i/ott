"""U04 ingestion and metadata-governance expand-only schema."""

import sqlalchemy as sa
from alembic import op

revision = "0004_u04_ingestion_expand"
down_revision = "0003_u03_catalog_expand"
branch_labels = None
depends_on = None
SCHEMA = "u04_ingestion"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "provider_policies",
        sa.Column("policy_id", sa.String(120), primary_key=True),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("provider_id", "version", name="uq_u04_provider_policy_version"),
        sa.CheckConstraint("version > 0", name="ck_u04_policy_version_positive"),
        schema=SCHEMA,
    )
    op.create_table(
        "ingestion_jobs",
        sa.Column("job_id", sa.String(120), primary_key=True),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column(
            "policy_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.provider_policies.policy_id"),
            nullable=False,
        ),
        sa.Column("lane", sa.String(40), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("start_cursor", sa.String(1000)),
        sa.Column("durable_cursor", sa.String(1000)),
        sa.Column("claim_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(120)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u04_job_claim",
        "ingestion_jobs",
        ["lane", "status", "available_at", "priority", "job_id"],
        schema=SCHEMA,
    )
    op.create_index("ix_u04_job_lease", "ingestion_jobs", ["lease_until", "status"], schema=SCHEMA)
    op.create_table(
        "ingestion_attempts",
        sa.Column("attempt_id", sa.String(120), primary_key=True),
        sa.Column(
            "job_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.ingestion_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(120), nullable=False),
        sa.Column("claim_version", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("outcome", sa.String(40)),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_u04_job_attempt"),
        schema=SCHEMA,
    )
    op.create_table(
        "raw_metadata",
        sa.Column("raw_record_id", sa.String(120), primary_key=True),
        sa.Column(
            "job_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.ingestion_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("provider_record_id", sa.String(300), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("payload_body", sa.LargeBinary()),
        sa.Column("payload_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_id", sa.String(120), nullable=False),
        sa.Column("tombstone_kind", sa.String(30)),
        sa.UniqueConstraint(
            "provider_id", "provider_record_id", "payload_digest", name="uq_u04_raw_digest"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u04_raw_expiry",
        "raw_metadata",
        ["payload_expires_at", "raw_record_id"],
        schema=SCHEMA,
        postgresql_where=sa.text("payload_body IS NOT NULL"),
    )
    op.create_table(
        "normalized_metadata",
        sa.Column("normalized_id", sa.String(120), primary_key=True),
        sa.Column(
            "raw_record_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.raw_metadata.raw_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("normalization_version", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "raw_record_id", "normalization_version", name="uq_u04_normalized_version"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "identity_resolutions",
        sa.Column("resolution_id", sa.String(120), primary_key=True),
        sa.Column(
            "normalized_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.normalized_metadata.normalized_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("selected_content_id", sa.String(120)),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.UniqueConstraint("normalized_id", "policy_version", name="uq_u04_identity_attempt"),
        schema=SCHEMA,
    )
    op.create_table(
        "merged_metadata",
        sa.Column("merged_id", sa.String(120), primary_key=True),
        sa.Column("canonical_content_id", sa.String(120), nullable=False),
        sa.Column("merge_policy_version", sa.String(80), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("canonical_content_id", "input_digest", name="uq_u04_merge_input"),
        schema=SCHEMA,
    )
    op.create_table(
        "validation_rule_versions",
        sa.Column("rule_version", sa.String(80), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("compatible_u03_version", sa.String(40), nullable=False),
        sa.Column("compatible_u05_version", sa.String(40), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "validation_runs",
        sa.Column("run_id", sa.String(120), primary_key=True),
        sa.Column(
            "merged_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.merged_metadata.merged_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rule_version",
            sa.String(80),
            sa.ForeignKey(f"{SCHEMA}.validation_rule_versions.rule_version"),
            nullable=False,
        ),
        sa.Column("attempt_key", sa.String(160), nullable=False, unique=True),
        sa.Column("trigger", sa.String(30), nullable=False),
        sa.Column("actor_reference", sa.String(120)),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "validation_decisions",
        sa.Column("decision_id", sa.String(120), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.validation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("state", sa.String(40), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("publication_key", sa.String(160), unique=True),
        sa.Column("catalog_version", sa.BigInteger(), unique=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u04_decision_pending",
        "validation_decisions",
        ["state", "decided_at", "decision_id"],
        schema=SCHEMA,
    )
    op.create_table(
        "quarantine_records",
        sa.Column("quarantine_id", sa.String(120), primary_key=True),
        sa.Column(
            "decision_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.validation_decisions.decision_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("resolution", sa.String(40), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("latest_attempt_id", sa.String(120)),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u04_quarantine_open",
        "quarantine_records",
        ["resolution", "opened_at", "quarantine_id"],
        schema=SCHEMA,
    )
    op.create_table(
        "publication_receipts",
        sa.Column("publication_key", sa.String(160), primary_key=True),
        sa.Column(
            "decision_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.validation_decisions.decision_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "retention_progress",
        sa.Column("provider_id", sa.String(80), primary_key=True),
        sa.Column("last_raw_record_id", sa.String(120)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )


def downgrade() -> None:
    raise RuntimeError("Automatic down migration is prohibited; use forward recovery")
