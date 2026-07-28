"""SQLAlchemy rows owned by the u03_catalog schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ott_feed.platform.adapters.database import Base

SCHEMA = "u03_catalog"


class ApprovedContentRow(Base):
    __tablename__ = "approved_contents"
    __table_args__ = {"schema": SCHEMA}
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(40), index=True)
    state: Mapped[str] = mapped_column(String(20), index=True)
    current_revision: Mapped[int] = mapped_column(Integer)
    catalog_version: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    release_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    runtime_minutes: Mapped[int | None]
    popularity: Mapped[float] = mapped_column(Float, index=True)
    genres: Mapped[list[str]] = mapped_column(JSON)
    current_decision_id: Mapped[str] = mapped_column(String(120), unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CatalogRevisionRow(Base):
    __tablename__ = "catalog_revisions"
    __table_args__ = (
        UniqueConstraint("decision_id", name="uq_catalog_decision"),
        {"schema": SCHEMA},
    )
    content_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"), primary_key=True
    )
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[str] = mapped_column(String(120))
    catalog_version: Mapped[int] = mapped_column(Integer, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContentLocalizationRow(Base):
    __tablename__ = "content_localizations"
    __table_args__ = {"schema": SCHEMA}
    content_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    synopsis: Mapped[str] = mapped_column(String(4000))
    people: Mapped[list[str]] = mapped_column(JSON)


class CatalogSourceRow(Base):
    __tablename__ = "catalog_sources"
    __table_args__ = {"schema": SCHEMA}
    content_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(200))
    license_reference: Mapped[str] = mapped_column(String(300))
    last_success_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ContentAvailabilityRow(Base):
    __tablename__ = "content_availability"
    __table_args__ = {"schema": SCHEMA}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    content_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.approved_contents.content_id", ondelete="CASCADE"), index=True
    )
    region: Mapped[str] = mapped_column(String(8), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    verified: Mapped[bool] = mapped_column(Boolean)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    direct_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    detail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class FeedProjectionGenerationRow(Base):
    __tablename__ = "feed_projection_generations"
    __table_args__ = {"schema": SCHEMA}
    generation_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    state: Mapped[str] = mapped_column(String(20), index=True)
    catalog_version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeedProjectionEntryRow(Base):
    __tablename__ = "feed_projection_entries"
    __table_args__ = {"schema": SCHEMA}
    generation_id: Mapped[str] = mapped_column(
        ForeignKey(f"{SCHEMA}.feed_projection_generations.generation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    section: Mapped[str] = mapped_column(String(30), primary_key=True)
    content_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    score: Mapped[float] = mapped_column(Float, index=True)


class ActiveProjectionGenerationRow(Base):
    __tablename__ = "active_projection_generations"
    __table_args__ = {"schema": SCHEMA}
    projection: Mapped[str] = mapped_column(String(40), primary_key=True)
    generation_id: Mapped[str] = mapped_column(String(80))
    previous_generation_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, default=1)


class ProjectionEventReceiptRow(Base):
    __tablename__ = "projection_event_receipts"
    __table_args__ = {"schema": SCHEMA}
    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    projection: Mapped[str] = mapped_column(String(40), primary_key=True)
    content_id: Mapped[str] = mapped_column(String(120), index=True)
    catalog_version: Mapped[int]
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectionVersionStateRow(Base):
    __tablename__ = "projection_version_state"
    __table_args__ = {"schema": SCHEMA}
    projection: Mapped[str] = mapped_column(String(40), primary_key=True)
    last_contiguous_version: Mapped[int] = mapped_column(Integer, default=0)


class ProjectionGapRow(Base):
    __tablename__ = "projection_gaps"
    __table_args__ = {"schema": SCHEMA}
    projection: Mapped[str] = mapped_column(String(40), primary_key=True)
    missing_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
