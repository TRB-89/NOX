"""
NØX - Database Models & DAO Operations
Safe parameterized operations for logging detection events and querying telemetry stats.
"""

from typing import List, Dict, Any, Optional
from backend.database.db import get_db_connection


class DetectionEventDAO:
    """Data Access Object for detection_events SQLite table."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def insert_event(
        self,
        timestamp: str,
        prediction: str,
        class_id: int,
        attack_score: float,
        threshold: float,
        severity: str,
        model_version: str,
        source_type: str,
    ) -> int:
        """Inserts a single detection event and returns its ID."""
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO detection_events (
                    timestamp, prediction, class_id, attack_score,
                    threshold, severity, model_version, source_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    prediction,
                    class_id,
                    attack_score,
                    threshold,
                    severity,
                    model_version,
                    source_type,
                ),
            )
            event_id = cursor.lastrowid
        conn.close()
        return event_id

    def insert_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Batch inserts multiple detection events inside a single transaction."""
        if not events:
            return 0
        conn = get_db_connection(self.db_path)
        with conn:
            conn.executemany(
                """
                INSERT INTO detection_events (
                    timestamp, prediction, class_id, attack_score,
                    threshold, severity, model_version, source_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        e["timestamp"],
                        e["prediction"],
                        e["class_id"],
                        e["attack_score"],
                        e["threshold"],
                        e["severity"],
                        e["model_version"],
                        e["source_type"],
                    )
                    for e in events
                ],
            )
        conn.close()
        return len(events)

    def get_recent_history(
        self,
        limit: int = 50,
        offset: int = 0,
        source_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves paginated detection history ordered by newest first."""
        conn = get_db_connection(self.db_path)
        query = "SELECT * FROM detection_events"
        params = []
        if source_type:
            query += " WHERE source_type = ?"
            params.append(source_type)
        query += " ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return results

    def get_telemetry_stats(self) -> Dict[str, Any]:
        """Calculates live dashboard statistics from stored detection events."""
        conn = get_db_connection(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM detection_events").fetchone()[0]
        normal_count = conn.execute("SELECT COUNT(*) FROM detection_events WHERE class_id = 0").fetchone()[0]
        attack_count = conn.execute("SELECT COUNT(*) FROM detection_events WHERE class_id = 1").fetchone()[0]

        severity_rows = conn.execute(
            "SELECT severity, COUNT(*) FROM detection_events GROUP BY severity"
        ).fetchall()
        severity_dist = {row[0]: row[1] for row in severity_rows}
        # Ensure default keys
        for s in ["Normal", "Low", "Medium", "High"]:
            if s not in severity_dist:
                severity_dist[s] = 0

        latest_row = conn.execute("SELECT timestamp FROM detection_events ORDER BY id DESC LIMIT 1").fetchone()
        latest_ts = latest_row[0] if latest_row else None
        conn.close()

        return {
            "total_records_analyzed": total,
            "predicted_normal_count": normal_count,
            "predicted_malicious_count": attack_count,
            "attack_percentage": round((attack_count / total * 100), 2) if total > 0 else 0.0,
            "severity_distribution": severity_dist,
            "most_recent_detection_timestamp": latest_ts,
        }
