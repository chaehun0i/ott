"""Search projection rows under u03_catalog."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.catalog.adapters.persistence.models import SCHEMA
from ott_feed.platform.adapters.database import Base


class SearchProjectionGenerationRow(Base):
    __tablename__ = "search_projection_generations"
    __table_args__ = {"schema": SCHEMA}
    generation_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    state: Mapped[str] = mapped_column(String(20), index=True)
    catalog_version: Mapped[int]
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding_dimension: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SearchDocumentRow(Base):
    __tablename__ = "search_documents"
    __table_args__ = {"schema": SCHEMA}
    generation_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.search_projection_generations.generation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    locale: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    normalized_title: Mapped[str] = mapped_column(String(500), index=True)
    people: Mapped[list[str]] = mapped_column(JSON)
    filters: Mapped[dict[str, Any]] = mapped_column(JSON)
    popularity: Mapped[float] = mapped_column(Float)


class ContentEmbeddingRow(Base):
    __tablename__ = "content_embeddings"
    __table_args__ = {"schema": SCHEMA}
    generation_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.search_projection_generations.generation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    locale: Mapped[str] = mapped_column(String(20), primary_key=True)
    model: Mapped[str] = mapped_column(String(120))
    dimension: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))


class SearchQualityRunRow(Base):
    __tablename__ = "search_quality_runs"
    __table_args__ = {"schema": SCHEMA}
    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    generation_id: Mapped[str] = mapped_column(String(80), index=True)
    locale: Mapped[str] = mapped_column(String(20))
    recall_at_10: Mapped[float] = mapped_column(Float)
    ndcg_at_10: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
