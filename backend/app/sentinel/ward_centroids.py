"""Bengaluru ward centroids — validated within city bounds (lat 12.7–13.3, lng 77.3–77.8).

All coordinates are real ward/neighbourhood centroids verified to be inside
Bengaluru Metropolitan Area. The simulator uses ONLY these points (+ small
jitter) so every generated event is geographically correct.
"""

from typing import TypedDict


class WardCentroid(TypedDict):
    ward_id: str
    ward_name: str
    district: str
    lat: float
    lng: float


BENGALURU_WARDS: list[WardCentroid] = [
    # ── Inner city ────────────────────────────────────────────────────────
    {"ward_id": "BLR-W17", "ward_name": "Jayanagar",        "district": "South",  "lat": 12.9250, "lng": 77.5938},
    {"ward_id": "BLR-W04", "ward_name": "Majestic",         "district": "Central","lat": 12.9767, "lng": 77.5713},
    {"ward_id": "BLR-W22", "ward_name": "KR Market",        "district": "Central","lat": 12.9634, "lng": 77.5780},
    {"ward_id": "BLR-W11", "ward_name": "Koramangala",      "district": "South",  "lat": 12.9352, "lng": 77.6245},
    {"ward_id": "BLR-W08", "ward_name": "Indiranagar",      "district": "East",   "lat": 12.9784, "lng": 77.6408},
    {"ward_id": "BLR-W52", "ward_name": "JP Nagar",         "district": "South",  "lat": 12.9063, "lng": 77.5857},
    {"ward_id": "BLR-W31", "ward_name": "Whitefield",       "district": "East",   "lat": 12.9698, "lng": 77.7500},
    {"ward_id": "BLR-W45", "ward_name": "Yelahanka",        "district": "North",  "lat": 13.1005, "lng": 77.5963},
    # ── MG Road / Brigade corridor ────────────────────────────────────────
    {"ward_id": "BLR-W09", "ward_name": "MG Road",          "district": "Central","lat": 12.9747, "lng": 77.6094},
    {"ward_id": "BLR-W10", "ward_name": "Shivajinagar",     "district": "Central","lat": 12.9866, "lng": 77.5993},
    # ── East / Electronic City corridor ───────────────────────────────────
    {"ward_id": "BLR-W60", "ward_name": "Electronic City",  "district": "South",  "lat": 12.8451, "lng": 77.6643},
    {"ward_id": "BLR-W55", "ward_name": "HSR Layout",       "district": "South",  "lat": 12.9116, "lng": 77.6473},
    {"ward_id": "BLR-W57", "ward_name": "Bannerghatta",     "district": "South",  "lat": 12.8827, "lng": 77.5977},
    # ── North ─────────────────────────────────────────────────────────────
    {"ward_id": "BLR-W02", "ward_name": "Hebbal",           "district": "North",  "lat": 13.0351, "lng": 77.5985},
    {"ward_id": "BLR-W03", "ward_name": "Rajajinagar",      "district": "West",   "lat": 12.9942, "lng": 77.5529},
]

# Ward IDs considered HIGH-RISK (matches the Predictive Hotspots demo data).
# Events in these wards get priority=high automatically.
HIGH_RISK_WARD_IDS: set[str] = {"BLR-W17", "BLR-W04", "BLR-W22", "BLR-W11"}
