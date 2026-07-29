"""U05 SQLAlchemy persistence rows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.platform.adapters.database import Base

SCHEMA = "u05_recommendation"


class RecommendationSessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("owner_id", "session_id", name="uq_u05_session_owner"),
        {"schema": SCHEMA},
    )
    session_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(120), nullable=False)
    epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    intent: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationRequestRow(Base):
    __tablename__ = "requests"
    __table_args__ = (
        UniqueConstraint("owner_id", "idempotency_key", name="uq_u05_request_idempotency"),
        {"schema": SCHEMA},
    )
    request_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(120))
    intent_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationPolicyRow(Base):
    __tablename__ = "policy_versions"
    __table_args__ = (
        UniqueConstraint("kind", "version", name="uq_u05_policy_kind_version"),
        {"schema": SCHEMA},
    )
    policy_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    configuration: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RankingProofRow(Base):
    __tablename__ = "ranking_proofs"
    __table_args__ = (
        UniqueConstraint("request_id", "position", name="uq_u05_ranking_position"),
        {"schema": SCHEMA},
    )
    ranking_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_version: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    proof: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ValidationOutcomeRow(Base):
    __tablename__ = "validation_outcomes"
    __table_args__ = (
        UniqueConstraint("request_id", "content_id", "claim_key", name="uq_u05_validation_claim"),
        {"schema": SCHEMA},
    )
    validation_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(120), nullable=False)
    claim_key: Mapped[str] = mapped_column(String(160), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(80), nullable=False)


class RecommendationTraceRow(Base):
    __tablename__ = "traces"
    __table_args__ = (Index("ix_u05_trace_retention", "expires_at", "trace_id"), {"schema": SCHEMA})
    trace_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    owner_reference: Mapped[str] = mapped_column(String(120), nullable=False)
    versions: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AIUsageRow(Base):
    __tablename__ = "ai_usage"
    usage_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_units: Mapped[int] = mapped_column(Integer, nullable=False)
    output_units: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetentionCheckpointRow(Base):
    __tablename__ = "retention_checkpoints"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    cursor: Mapped[str | None] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
