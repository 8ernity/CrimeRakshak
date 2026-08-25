"""Pydantic schemas for the Sentinel Grid API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SensorEventOut(BaseModel):
    """Single sensor event — serialised for WebSocket / REST responses."""

    id: int
    sensor_id: str
    sensor_type: Literal["cctv_alert", "anpr_hit", "sos_button", "gunshot"]
    lat: float
    lng: float
    ward_id: Optional[str] = None
    ward_name: Optional[str] = None
    district: Optional[str] = None
    confidence: float
    priority: Literal["high", "normal"]
    metadata: Optional[dict[str, Any]] = Field(None, alias="metadata_")
    linked_case_id: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class SentinelSummary(BaseModel):
    """Aggregate KPI counts for the Sentinel Grid header strip."""

    active_sensors: int = Field(description="Distinct sensor IDs seen in the last hour")
    events_last_24h: int = Field(description="Total events in the last 24 hours")
    high_priority_active: int = Field(description="High-priority events in the last hour")
    cases_auto_linked: int = Field(description="Events with a linked Neo4j case")


class SentinelEventsResponse(BaseModel):
    events: list[SensorEventOut]
    total: int
    source: Literal["live", "demo"]


class SentinelSummaryResponse(SentinelSummary):
    source: Literal["live", "demo"]
