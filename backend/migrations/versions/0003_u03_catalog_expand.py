"""U03 approved catalog and discovery expand-only schema."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0003_u03_catalog_expand"
down_revision = "0002_u02_identity_expand"
branch_labels = None
depends_on = None
SCHEMA = "u03_catalog"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE SCHEMA IF NOT EXISTS u03_catalog")
    op.create_table(
        "approved_contents",
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("content_type", sa.String(40), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("current_revision", sa.Integer(), nullable=False),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("release_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runtime_minutes", sa.Integer()),
        sa.Column("popularity", sa.Float(), nullable=False),
        sa.Column("genres", sa.JSON(), nullable=False),
        sa.Column("current_decision_id", sa.String(120), nullable=False, unique=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("catalog_version > 0", name="ck_catalog_version_positive"),
        sa.CheckConstraint("popularity >= 0 AND popularity <= 1", name="ck_popularity_range"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_catalog_state_release", "approved_contents", ["state", "release_at"], schema=SCHEMA
    )
    op.create_table(
        "catalog_revisions",
        sa.Column(
            "content_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("decision_id", sa.String(120), nullable=False, unique=True),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "content_localizations",
        sa.Column(
            "content_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("locale", sa.String(20), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("synopsis", sa.String(4000), nullable=False),
        sa.Column("people", sa.JSON(), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_localization_title_trgm",
        "content_localizations",
        ["title"],
        schema=SCHEMA,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_table(
        "catalog_sources",
        sa.Column(
            "content_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("provider", sa.String(80), primary_key=True),
        sa.Column("source_record_id", sa.String(200), nullable=False),
        sa.Column("license_reference", sa.String(300), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "content_availability",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "content_id",
            sa.String(120),
            sa.ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("direct_url", sa.String(1000)),
        sa.Column("detail_url", sa.String(1000)),
        sa.CheckConstraint(
            "direct_url IS NOT NULL OR detail_url IS NOT NULL", name="ck_availability_link"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_availability_closure",
        "content_availability",
        ["content_id", "region", "verified", "starts_at", "ends_at"],
        schema=SCHEMA,
    )
    op.create_table(
        "feed_projection_generations",
        sa.Column("generation_id", sa.String(80), primary_key=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "feed_projection_entries",
        sa.Column(
            "generation_id",
            sa.String(80),
            sa.ForeignKey(
                f"{SCHEMA}.feed_projection_generations.generation_id", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column("section", sa.String(30), primary_key=True),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("score", sa.Float(), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_feed_page",
        "feed_projection_entries",
        ["generation_id", "section", "score", "content_id"],
        schema=SCHEMA,
    )
    op.create_table(
        "search_projection_generations",
        sa.Column("generation_id", sa.String(80), primary_key=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "search_documents",
        sa.Column(
            "generation_id",
            sa.String(80),
            sa.ForeignKey(
                f"{SCHEMA}.search_projection_generations.generation_id", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("locale", sa.String(20), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.String(500), nullable=False),
        sa.Column("people", sa.JSON(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("popularity", sa.Float(), nullable=False),
        sa.Column("search_vector", sa.Text()),
        schema=SCHEMA,
    )
    op.execute(
        "CREATE INDEX ix_search_fts ON u03_catalog.search_documents USING gin "
        "(to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(search_vector,'')))"
    )
    op.create_index(
        "ix_search_title_trgm",
        "search_documents",
        ["normalized_title"],
        schema=SCHEMA,
        postgresql_using="gin",
        postgresql_ops={"normalized_title": "gin_trgm_ops"},
    )
    op.create_table(
        "content_embeddings",
        sa.Column(
            "generation_id",
            sa.String(80),
            sa.ForeignKey(
                f"{SCHEMA}.search_projection_generations.generation_id", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column("content_id", sa.String(120), primary_key=True),
        sa.Column("locale", sa.String(20), primary_key=True),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_embedding_hnsw",
        "content_embeddings",
        ["embedding"],
        schema=SCHEMA,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_table(
        "active_projection_generations",
        sa.Column("projection", sa.String(40), primary_key=True),
        sa.Column("generation_id", sa.String(80), nullable=False),
        sa.Column("previous_generation_id", sa.String(80)),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        schema=SCHEMA,
    )
    op.create_table(
        "projection_event_receipts",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("projection", sa.String(40), primary_key=True),
        sa.Column("content_id", sa.String(120), nullable=False),
        sa.Column("catalog_version", sa.BigInteger(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "projection_version_state",
        sa.Column("projection", sa.String(40), primary_key=True),
        sa.Column("last_contiguous_version", sa.BigInteger(), nullable=False, server_default="0"),
        schema=SCHEMA,
    )
    op.create_table(
        "projection_gaps",
        sa.Column("projection", sa.String(40), primary_key=True),
        sa.Column("missing_version", sa.BigInteger(), primary_key=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )
    op.create_table(
        "search_quality_runs",
        sa.Column("run_id", sa.String(80), primary_key=True),
        sa.Column("generation_id", sa.String(80), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("recall_at_10", sa.Float(), nullable=False),
        sa.Column("ndcg_at_10", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_outbox_u03_claim",
        "outbox_jobs",
        ["lane", "status", "available_at", "job_type"],
        postgresql_where=sa.text("job_type LIKE 'u03.%'"),
    )


def downgrade() -> None:
    raise RuntimeError("Automatic down migration is prohibited; use forward recovery")
