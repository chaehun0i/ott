"""U05 recommendation and AI grounding expand migration."""

import sqlalchemy as sa
from alembic import op

revision = "0005_u05_recommendation_expand"
down_revision = "0004_u04_ingestion_expand"
branch_labels = None
depends_on = None
SCHEMA = "u05_recommendation"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(120), primary_key=True),
        sa.Column("owner_id", sa.String(120), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("intent", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(160), unique=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "session_id", name="uq_u05_session_owner"),
        schema=SCHEMA,
    )
    op.create_table(
        "requests",
        sa.Column("request_id", sa.String(120), primary_key=True),
        sa.Column("owner_id", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("session_id", sa.String(120)),
        sa.Column("intent_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "idempotency_key", name="uq_u05_request_idempotency"),
        schema=SCHEMA,
    )
    op.create_table(
        "policy_versions",
        sa.Column("policy_id", sa.String(120), primary_key=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("kind", "version", name="uq_u05_policy_kind_version"),
        schema=SCHEMA,
    )
    op.create_table(
        "ranking_proofs",
        sa.Column("ranking_id", sa.String(120), primary_key=True),
        sa.Column("request_id", sa.String(120), nullable=False),
        sa.Column("content_id", sa.String(120), nullable=False),
        sa.Column("metadata_version", sa.String(80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("proof", sa.JSON(), nullable=False),
        sa.UniqueConstraint("request_id", "position", name="uq_u05_ranking_position"),
        schema=SCHEMA,
    )
    op.create_index("ix_u05_ranking_request", "ranking_proofs", ["request_id"], schema=SCHEMA)
    op.create_table(
        "validation_outcomes",
        sa.Column("validation_id", sa.String(120), primary_key=True),
        sa.Column("request_id", sa.String(120), nullable=False),
        sa.Column("content_id", sa.String(120), nullable=False),
        sa.Column("claim_key", sa.String(160), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("rule_version", sa.String(80), nullable=False),
        sa.UniqueConstraint(
            "request_id", "content_id", "claim_key", name="uq_u05_validation_claim"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_u05_validation_request", "validation_outcomes", ["request_id"], schema=SCHEMA
    )
    op.create_table(
        "traces",
        sa.Column("trace_id", sa.String(120), primary_key=True),
        sa.Column("request_id", sa.String(120), nullable=False, unique=True),
        sa.Column("owner_reference", sa.String(120), nullable=False),
        sa.Column("versions", sa.JSON(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index("ix_u05_trace_retention", "traces", ["expires_at", "trace_id"], schema=SCHEMA)
    op.create_table(
        "ai_usage",
        sa.Column("usage_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(120), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("input_units", sa.Integer(), nullable=False),
        sa.Column("output_units", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index("ix_u05_usage_request", "ai_usage", ["request_id"], schema=SCHEMA)
    op.create_table(
        "retention_checkpoints",
        sa.Column("name", sa.String(80), primary_key=True),
        sa.Column("cursor", sa.String(120)),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )


def downgrade() -> None:
    raise RuntimeError("Automatic down migration is prohibited; use forward recovery")
