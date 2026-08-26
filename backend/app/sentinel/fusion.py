"""Hotspot-fusion logic for Sentinel Grid.

Computes the priority of an incoming sensor event by crossing it against the
known high-risk ward set. High-risk wards come from the Predictive Hotspots
dataset (hard-coded here to avoid a live ML call — same data the frontend
already uses).

Rules
-----
- Ward is in the HIGH_RISK set                 → priority = "high"
- Sensor type is ``sos_button`` or ``gunshot`` → priority = "high"
- Otherwise                                    → priority = "normal"
"""
from __future__ import annotations

from app.sentinel.ward_centroids import HIGH_RISK_WARD_IDS

# Sensor types that are always high-priority regardless of location.
_ALWAYS_HIGH_TYPES: frozenset[str] = frozenset({"sos_button", "gunshot"})


def compute_priority(ward_id: str | None, sensor_type: str) -> str:
    """Return ``"high"`` or ``"normal"`` for the event."""
    if sensor_type in _ALWAYS_HIGH_TYPES:
        return "high"
    if ward_id and ward_id in HIGH_RISK_WARD_IDS:
        return "high"
    return "normal"
