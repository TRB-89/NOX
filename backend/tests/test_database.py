"""
NØX - Unit Tests: Database Layer & SQLite Event Logging
Tests SQLite schema initialization, safe parameterized queries, pagination, and telemetry metrics.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from backend.database.db import init_db
from backend.database.models import DetectionEventDAO


@pytest.fixture
def temp_db(tmp_path):
    """Provides an isolated temporary SQLite database for testing."""
    db_file = tmp_path / "test_events.db"
    init_db(db_file)
    dao = DetectionEventDAO(str(db_file))
    return dao


def test_insert_and_get_history(temp_db):
    """Verifies event insertion and historical retrieval."""
    event_id = temp_db.insert_event(
        timestamp="2026-10-22T12:00:00Z",
        prediction="Potential Attack",
        class_id=1,
        attack_score=0.95,
        threshold=0.50,
        severity="High",
        model_version="NØX-MLP-v1",
        source_type="single",
    )
    assert event_id is not None
    assert event_id > 0

    history = temp_db.get_recent_history(limit=10)
    assert len(history) == 1
    assert history[0]["prediction"] == "Potential Attack"
    assert history[0]["class_id"] == 1
    assert history[0]["attack_score"] == 0.95
    assert history[0]["severity"] == "High"


def test_batch_insert_and_pagination(temp_db):
    """Verifies batch insertion and limit/offset pagination."""
    events = [
        {
            "timestamp": f"2026-10-22T12:0{i}:00Z",
            "prediction": "Normal Traffic" if i % 2 == 0 else "Potential Attack",
            "class_id": 0 if i % 2 == 0 else 1,
            "attack_score": 0.2 if i % 2 == 0 else 0.8,
            "threshold": 0.50,
            "severity": "Normal" if i % 2 == 0 else "Medium",
            "model_version": "NØX-MLP-v1",
            "source_type": "batch",
        }
        for i in range(10)
    ]
    inserted = temp_db.insert_events_batch(events)
    assert inserted == 10

    # Paginate: limit 4, offset 0
    page1 = temp_db.get_recent_history(limit=4, offset=0)
    assert len(page1) == 4

    # Paginate: limit 4, offset 4
    page2 = temp_db.get_recent_history(limit=4, offset=4)
    assert len(page2) == 4


def test_telemetry_stats_calculation(temp_db):
    """Verifies live statistical calculations."""
    temp_db.insert_event(
        timestamp="2026-10-22T12:00:00Z",
        prediction="Normal Traffic",
        class_id=0,
        attack_score=0.15,
        threshold=0.50,
        severity="Normal",
        model_version="NØX-MLP-v1",
        source_type="single",
    )
    temp_db.insert_event(
        timestamp="2026-10-22T12:05:00Z",
        prediction="Potential Attack",
        class_id=1,
        attack_score=0.92,
        threshold=0.50,
        severity="High",
        model_version="NØX-MLP-v1",
        source_type="single",
    )

    stats = temp_db.get_telemetry_stats()
    assert stats["total_records_analyzed"] == 2
    assert stats["predicted_normal_count"] == 1
    assert stats["predicted_malicious_count"] == 1
    assert stats["attack_percentage"] == 50.0
    assert stats["severity_distribution"]["High"] == 1
    assert stats["severity_distribution"]["Normal"] == 1
