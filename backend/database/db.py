"""
NØX - Database Layer
SQLite connection manager and schema initialization for detection event logging.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DB_FILE = Path(__file__).resolve().parent / "nox_events.db"


def get_db_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection with row factory configured."""
    target_path = Path(db_path) if db_path else DB_FILE
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path | str] = None) -> None:
    """Initializes the detection_events table and required indexes."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prediction TEXT NOT NULL,
                class_id INTEGER NOT NULL,
                attack_score REAL NOT NULL,
                threshold REAL NOT NULL,
                severity TEXT NOT NULL,
                model_version TEXT NOT NULL,
                source_type TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON detection_events(timestamp DESC);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_prediction ON detection_events(prediction);
        """)
    conn.close()
