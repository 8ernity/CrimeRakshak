"""Sentinel Grid — FastAPI router.

Endpoints
---------
GET  /api/v1/sentinel/events   — paginated event list (filterable)
GET  /api/v1/sentinel/summary  — KPI summary counts
WS   /ws/sentinel-grid         — real-time WebSocket stream
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.sentinel.models import SensorEvent, Priority, SensorType
from app.sentinel.schemas import (
    SentinelEventsResponse,
    SentinelSummaryResponse,
    SensorEventOut,
)
from app.sentinel import simulator as sim

logger = logging.getLogger("sentinel.router")

router = APIRouter(prefix="/sentinel", tags=["sentinel"])
ws_router = APIRouter(tags=["sentinel-ws"])


# ─────────────────────────────────────────────────────────────────────────────
# REST — /sentinel/summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=SentinelSummaryResponse, summary="Sentinel KPI summary")
def get_summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    h1_ago = now - timedelta(hours=1)
    h24_ago = now - timedelta(hours=24)

    active_sensors = db.execute(
        select(func.count(func.distinct(SensorEvent.sensor_id))).where(
            SensorEvent.timestamp >= h1_ago
        )
    ).scalar_one()

    events_24h = db.execute(
        select(func.count()).where(SensorEvent.timestamp >= h24_ago)
    ).scalar_one()

    high_priority = db.execute(
        select(func.count()).where(
            and_(SensorEvent.priority == Priority.high, SensorEvent.timestamp >= h1_ago)
        )
    ).scalar_one()

    auto_linked = db.execute(
        select(func.count()).where(SensorEvent.linked_case_id.isnot(None))
    ).scalar_one()

    return SentinelSummaryResponse(
        active_sensors=active_sensors,
        events_last_24h=events_24h,
        high_priority_active=high_priority,
        cases_auto_linked=auto_linked,
        source="live",
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST — /sentinel/events
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events", response_model=SentinelEventsResponse, summary="List sensor events")
def list_events(
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    priority: Optional[Literal["high", "normal"]] = Query(None),
    sensor_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(SensorEvent).order_by(desc(SensorEvent.timestamp))

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            stmt = stmt.where(SensorEvent.timestamp >= since_dt)
        except ValueError:
            pass

    if priority:
        stmt = stmt.where(SensorEvent.priority == Priority(priority))

    if sensor_type and sensor_type in {st.value for st in SensorType}:
        stmt = stmt.where(SensorEvent.sensor_type == SensorType(sensor_type))

    rows = db.execute(stmt.limit(limit)).scalars().all()
    total = db.execute(select(func.count()).select_from(SensorEvent)).scalar_one()

    events = [SensorEventOut.model_validate(r) for r in rows]
    return SentinelEventsResponse(events=events, total=total, source="live")


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket — /ws/sentinel-grid
# ─────────────────────────────────────────────────────────────────────────────

@ws_router.websocket("/ws/sentinel-grid")
async def sentinel_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected: %s", websocket.client)

    async def _send(message: str) -> None:
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    sim.register_ws_client(_send)
    try:
        while True:
            # Keep-alive: wait for client ping or disconnect
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                # Send server-side keep-alive
                await websocket.send_text('{"type":"heartbeat"}')
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", websocket.client)
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        sim.unregister_ws_client(_send)
