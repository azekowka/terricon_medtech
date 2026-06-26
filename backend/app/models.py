"""SQLAlchemy ORM models.

Implements the data structure from TZ 2.2 plus the supporting tables required by
the functional/non-functional requirements:

  * raw layer separate from normalized layer        (TZ 3.1)
  * deduplication via a stable dedup_key            (TZ 3.1)
  * parse error/event journaling                    (TZ 3.1)
  * unmatched (manual-labelling) queue              (TZ 3.2)
  * price-change history                            (TZ 3.4)
  * price subscriptions                             (TZ 3.4)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Service(Base):
    """Canonical service dictionary entry (TZ 3.2: id, name, synonyms, category)."""

    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    specialty: Mapped[str] = mapped_column(String(128), default="", index=True)
    tarif_code: Mapped[str] = mapped_column(String(32), default="")
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    base_price_kzt: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    prices: Mapped[list[Price]] = relationship(back_populates="service")


class Clinic(Base):
    """A clinic / lab branch (TZ 2.2 clinic_* fields)."""

    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str] = mapped_column(String(64), index=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    working_hours: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(64), index=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_online_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    prices: Mapped[list[Price]] = relationship(back_populates="clinic")

    __table_args__ = (
        UniqueConstraint("name", "city", "source", name="uq_clinic_name_city_source"),
    )


class RawPrice(Base):
    """Raw scraped row, stored *before* normalization (TZ 3.1: raw layer)."""

    __tablename__ = "raw_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(String(512), default="")
    clinic_name_raw: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(64), default="")
    service_name_raw: Mapped[str] = mapped_column(String(512))
    price_raw: Mapped[str] = mapped_column(String(64), default="")
    currency: Mapped[str] = mapped_column(String(8), default="KZT")
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Price(Base):
    """Normalized, deduplicated price record (the layer the UI queries)."""

    __tablename__ = "prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), index=True)
    service_id: Mapped[str | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    service_name_raw: Mapped[str] = mapped_column(String(512))
    service_name_norm: Mapped[str] = mapped_column(String(255), default="")
    category: Mapped[str] = mapped_column(String(32), default="", index=True)
    price_kzt: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="KZT")
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(String(512), default="")
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Stable key for dedup/upsert across re-runs (TZ 3.1).
    dedup_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    clinic: Mapped[Clinic] = relationship(back_populates="prices")
    service: Mapped[Service | None] = relationship(back_populates="prices")

    __table_args__ = (
        Index("ix_price_service_active", "service_id", "is_active"),
        Index("ix_price_category_active", "category", "is_active"),
    )


class PriceHistory(Base):
    """Append-only price observations for the history chart (TZ 3.4)."""

    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), index=True)
    service_id: Mapped[str | None] = mapped_column(ForeignKey("services.id"), nullable=True, index=True)
    price_kzt: Mapped[float] = mapped_column(Numeric(12, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class UnmatchedQueue(Base):
    """Raw names the normalizer could not confidently map (TZ 3.2: manual queue)."""

    __tablename__ = "unmatched_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    service_name_raw: Mapped[str] = mapped_column(String(512), index=True)
    source: Mapped[str] = mapped_column(String(64), default="")
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    suggested_service_id: Mapped[str | None] = mapped_column(
        ForeignKey("services.id"), nullable=True
    )
    suggested_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # pending/resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("service_name_raw", "source", name="uq_unmatched_raw_source"),
    )


class ParseLog(Base):
    """Per-run journal of parsing events / errors (TZ 3.1)."""

    __tablename__ = "parse_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="success")  # success/partial/error
    message: Mapped[str] = mapped_column(Text, default="")
    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_new: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Subscription(Base):
    """User subscription to a service/clinic price (TZ 3.4)."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), index=True)
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"), index=True)
    clinic_id: Mapped[str | None] = mapped_column(ForeignKey("clinics.id"), nullable=True)
    target_price_kzt: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
