"""Neo4j entity-linker for Sentinel Grid.

Tries to match an incoming sensor event against entities already in the
criminal-network graph. On a match it creates a ``DETECTED_AT`` relationship
and returns the linked case / entity ID. All failures are silently swallowed
so that Neo4j downtime never blocks sensor ingestion.

Demo scenario
-------------
ANPR events with plate number ``"KA01AB1234"`` are pre-wired to return a
fixed synthetic case ID so the frontend can demonstrate the "View linked case"
deep-link without requiring a live Neo4j instance.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("sentinel.linker")

# Demo plate → synthetic case mapping (shown when Neo4j is unavailable).
_DEMO_PLATE_CASES: dict[str, str] = {
    "KA01AB1234": "CASE-2024-00441",
    "KA05MX9988": "CASE-2024-00189",
}


def link_event_to_graph(
    sensor_type: str,
    event_metadata: dict[str, Any],
) -> str | None:
    """Attempt to link the event to a Neo4j node.

    Returns the linked ``case_id`` string on success, or ``None`` if the graph
    is unavailable or no matching entity was found.
    """
    # ── Demo path: ANPR plate matching ────────────────────────────────────
    if sensor_type == "anpr_hit":
        plate = event_metadata.get("plate_number", "")
        if plate in _DEMO_PLATE_CASES:
            logger.debug("ANPR demo match: plate=%s case=%s", plate, _DEMO_PLATE_CASES[plate])
            return _DEMO_PLATE_CASES[plate]

    # ── Live Neo4j path ───────────────────────────────────────────────────
    try:
        from app.graph.connection import graph_connection, GraphConnectionError

        if sensor_type == "anpr_hit":
            plate = event_metadata.get("plate_number")
            if not plate:
                return None

            rows = graph_connection.run_read(
                """
                MATCH (v:Vehicle {plate_number: $plate})-[:BELONGS_TO]->(s:Suspect)
                OPTIONAL MATCH (s)-[:INVOLVED_IN]->(c:Case)
                RETURN c.case_id AS case_id LIMIT 1
                """,
                {"plate": plate},
            )
            if rows and rows[0].get("case_id"):
                case_id = str(rows[0]["case_id"])
                # Write DETECTED_AT edge back to the graph
                graph_connection.run_write(
                    """
                    MATCH (v:Vehicle {plate_number: $plate})
                    MERGE (loc:Location {ward_id: $ward_id})
                      ON CREATE SET loc.name = $ward_name
                    MERGE (v)-[r:DETECTED_AT]->(loc)
                      ON CREATE SET r.first_seen = datetime()
                    SET r.last_seen = datetime()
                    """,
                    {
                        "plate": plate,
                        "ward_id": event_metadata.get("ward_id", "unknown"),
                        "ward_name": event_metadata.get("ward_name", "Unknown"),
                    },
                )
                return case_id

        if sensor_type == "sos_button":
            phone = event_metadata.get("phone_number")
            if not phone:
                return None
            rows = graph_connection.run_read(
                """
                MATCH (p:Person {phone: $phone})-[:INVOLVED_IN]->(c:Case)
                RETURN c.case_id AS case_id LIMIT 1
                """,
                {"phone": phone},
            )
            if rows and rows[0].get("case_id"):
                return str(rows[0]["case_id"])

    except Exception as exc:  # noqa: BLE001 — never block ingestion
        logger.debug("Neo4j link attempt failed (silent): %s", exc)

    return None
