"""SQLAlchemy ORM model for the ``sensor_events`` table.

Stored in the existing PostgreSQL instance. Uses plain FLOAT columns for
coordinates (no PostGIS extension required).
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from app.core.database import Base


class SensorType(str, enum.Enum):
    cctv_alert = "cctv_alert"
    anpr_hit = "anpr_hit"
    sos_button = "sos_button"
    gunshot = "gunshot"


class Priority(str, enum.Enum):
    high = "high"
    normal = "normal"


class SensorEvent(Base):
    """One raw sensor event ingested by the Sentinel Grid simulator."""

    __tablename__ = "sensor_events"

    id = Column(Integer, primary_key=True, index=True)

    sensor_id = Column(String(64), nullable=False)
    sensor_type = Column(Enum(SensorType), nullable=False)

    # Geographic position — Bengaluru bounds enforced by CHECK constraint
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    ward_id = Column(String(32), nullable=True)
    ward_name = Column(String(128), nullable=True)
    district = Column(String(64), nullable=True)

    confidence = Column(Float, nullable=False, default=0.85)
    priority = Column(Enum(Priority), nullable=False, default=Priority.normal)

    # Arbitrary extra metadata (plate number, audio snippet label, etc.)
    metadata_ = Column("metadata", JSON, nullable=True)

    # Set when this event has been linked to a criminal-network entity in Neo4j
    linked_case_id = Column(String(64), nullable=True, index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        # Bengaluru Metropolitan Area bounds
        CheckConstraint("lat >= 12.7 AND lat <= 13.3", name="ck_sensor_events_lat_bounds"),
        CheckConstraint("lng >= 77.3 AND lng <= 77.8", name="ck_sensor_events_lng_bounds"),
        Index("ix_sensor_events_timestamp", "timestamp"),
        Index("ix_sensor_events_priority", "priority"),
        Index("ix_sensor_events_sensor_type", "sensor_type"),
    )
