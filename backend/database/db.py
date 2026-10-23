"""
NØX - Database Layer
SQLite connection manager and schema initialization for detection event logging.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Default SQLite database file path.
# NOTE ON CLOUD HOSTING: On Render's free tier, local filesystem storage is ephemeral.
# Events logged to SQLite will reset upon container redeploy or idle shutdown.
_default_db_path = Path(__file__).resolve().parent / "nox_events.db"
DB_FILE = Path(os.getenv("NOX_DB_PATH", str(_default_db_path)))


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
