"""Sentinel Grid — in-process sensor event simulator.

Runs as a daemon background thread started at FastAPI startup. Generates
synthetic sensor events every 3–8 seconds using real Bengaluru ward centroids
plus small geographic jitter. Events are:

1. Persisted to PostgreSQL (``sensor_events`` table).
2. Priority-classified via :mod:`app.sentinel.fusion`.
3. Linked to the Neo4j graph when possible via :mod:`app.sentinel.neo4j_linker`.
4. Broadcast to all active WebSocket clients via the shared ``_ws_clients`` set.

No external MQTT broker is required — the simulator is the pipeline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import threading
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("sentinel.simulator")

# ── Shared state ─────────────────────────────────────────────────────────────
# Set of active WebSocket send-coroutines; mutated by the router.
_ws_clients: set[Any] = set()
_ws_lock = threading.Lock()

# Running flag — set to False on shutdown.
_running = False
_thread: threading.Thread | None = None


# ── Sensor templates ─────────────────────────────────────────────────────────

_SENSOR_TYPES = ["cctv_alert", "anpr_hit", "sos_button", "gunshot"]
_TYPE_WEIGHTS = [0.45, 0.30, 0.15, 0.10]   # cctv most common, gunshot rarest

# Demo ANPR plates — 10% of ANPR events use the first plate to trigger a
# Neo4j graph link in the demo scenario.
_DEMO_PLATES = ["KA01AB1234", "KA05MX9988", "KA03CD5678", "KA51EF7890", "KA09GH2345"]
_PHONE_NUMBERS = ["+91 98450 11111", "+91 80765 22222", "+91 73456 33333"]

_EVENT_COUNTER = 0


def _make_sensor_id(sensor_type: str, ward_id: str) -> str:
    prefix = {
        "cctv_alert": "CCTV",
        "anpr_hit": "ANPR",
        "sos_button": "SOS",
        "gunshot": "ACUS",
    }.get(sensor_type, "SENS")
    return f"{prefix}-{ward_id}-{random.randint(1, 12):02d}"


def _make_metadata(sensor_type: str, ward_id: str, ward_name: str) -> dict[str, Any]:
    base = {"ward_id": ward_id, "ward_name": ward_name}
    if sensor_type == "cctv_alert":
        base["object_detected"] = random.choice(["person", "vehicle", "crowd"])
        base["camera_model"] = random.choice(["Hikvision DS-2CD", "Dahua IPC-HFW", "Axis P3245"])
    elif sensor_type == "anpr_hit":
        # 10% chance of demo match plate (links to Neo4j in demo)
        if random.random() < 0.10:
            plate = _DEMO_PLATES[0]
        else:
            plate = random.choice(_DEMO_PLATES[1:])
        base["plate_number"] = plate
        base["vehicle_color"] = random.choice(["white", "black", "red", "silver", "blue"])
    elif sensor_type == "sos_button":
        base["phone_number"] = random.choice(_PHONE_NUMBERS)
        base["activation_method"] = random.choice(["button_press", "shake_gesture"])
    elif sensor_type == "gunshot":
        base["decibels"] = round(random.uniform(110.0, 145.0), 1)
        base["bearing_degrees"] = random.randint(0, 359)
    return base


def _generate_event(db_session) -> dict[str, Any] | None:
    """Create, persist, and return one synthetic sensor event."""
    global _EVENT_COUNTER

    from app.sentinel.ward_centroids import BENGALURU_WARDS
    from app.sentinel.fusion import compute_priority
    from app.sentinel.neo4j_linker import link_event_to_graph
    from app.sentinel.models import SensorEvent, SensorType, Priority

    ward = random.choice(BENGALURU_WARDS)

    # Small geographic jitter (±0.002° ≈ ±220 m) — stays within Bengaluru bounds
    lat = ward["lat"] + random.uniform(-0.002, 0.002)
    lng = ward["lng"] + random.uniform(-0.002, 0.002)

    sensor_type: str = random.choices(_SENSOR_TYPES, weights=_TYPE_WEIGHTS, k=1)[0]
    confidence = round(random.uniform(0.60, 0.99), 2)
    metadata = _make_metadata(sensor_type, ward["ward_id"], ward["ward_name"])
    priority = compute_priority(ward["ward_id"], sensor_type)

    _EVENT_COUNTER += 1
    sensor_id = _make_sensor_id(sensor_type, ward["ward_id"])
    ts = datetime.now(timezone.utc)

    # Link to Neo4j (always silently optional)
    linked_case_id = link_event_to_graph(sensor_type, {**metadata, **ward})

    try:
        event = SensorEvent(
            sensor_id=sensor_id,
            sensor_type=SensorType(sensor_type),
            lat=lat,
            lng=lng,
            ward_id=ward["ward_id"],
            ward_name=ward["ward_name"],
            district=ward["district"],
            confidence=confidence,
            priority=Priority(priority),
            metadata_=metadata,
            linked_case_id=linked_case_id,
            timestamp=ts,
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        return {
            "id": event.id,
            "sensor_id": event.sensor_id,
            "sensor_type": sensor_type,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "ward_id": ward["ward_id"],
            "ward_name": ward["ward_name"],
            "district": ward["district"],
            "confidence": confidence,
            "priority": priority,
            "metadata": metadata,
            "linked_case_id": linked_case_id,
            "timestamp": ts.isoformat(),
        }
    except Exception as exc:
        logger.error("Failed to persist sensor event: %s", exc)
        db_session.rollback()
        return None


def _broadcast(payload: dict[str, Any]) -> None:
    """Send JSON payload to all connected WebSocket clients (thread-safe)."""
    message = json.dumps({"type": "sensor_event", "data": payload})
    with _ws_lock:
        dead: list[Any] = []
        for send_fn in _ws_clients:
            try:
                # Enqueue coroutine in the event loop if one is running
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(send_fn(message), loop)
                    else:
                        raise RuntimeError("No running event loop")
                except RuntimeError:
                    dead.append(send_fn)
            except Exception:
                dead.append(send_fn)
        for fn in dead:
            _ws_clients.discard(fn)


def _simulator_loop() -> None:
    """Main simulator loop — runs in a daemon thread."""
    from app.core.database import SessionLocal

    logger.info("Sentinel simulator started.")
    db = SessionLocal()
    try:
        while _running:
            interval = random.uniform(3.0, 8.0)
            time.sleep(interval)
            if not _running:
                break
            event = _generate_event(db)
            if event:
                logger.debug(
                    "Generated event: type=%s ward=%s priority=%s linked=%s",
                    event["sensor_type"],
                    event["ward_name"],
                    event["priority"],
                    event["linked_case_id"],
                )
                _broadcast(event)
    except Exception as exc:
        logger.error("Simulator loop crashed: %s", exc, exc_info=True)
    finally:
        db.close()
        logger.info("Sentinel simulator stopped.")


def start_simulator() -> None:
    """Start the background simulator thread. Called once at app startup."""
    global _running, _thread
    if _thread and _thread.is_alive():
        return  # Already running
    _running = True
    _thread = threading.Thread(target=_simulator_loop, name="sentinel-simulator", daemon=True)
    _thread.start()
    logger.info("Sentinel simulator thread launched.")


def stop_simulator() -> None:
    """Signal the simulator thread to exit. Called at app shutdown."""
    global _running
    _running = False
    logger.info("Sentinel simulator stop requested.")


def register_ws_client(send_fn) -> None:
    with _ws_lock:
        _ws_clients.add(send_fn)


def unregister_ws_client(send_fn) -> None:
    with _ws_lock:
        _ws_clients.discard(send_fn)
