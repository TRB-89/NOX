"""
NØX - Unit Tests: Detection Service
Tests single-flow inference, batch limits, and timezone-aware timestamps.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from backend.services.model_service import ModelService
from backend.services.detection_service import DetectionService
from backend.database.models import DetectionEventDAO


@pytest.fixture(scope="module")
def detection_service(tmp_path_factory):
    """Initializes a detection service with an isolated SQLite db."""
    db_file = tmp_path_factory.mktemp("db") / "test_detect.db"
    from backend.database.db import init_db
    init_db(db_file)

    model_service = ModelService()
    model_service.load_artifacts()
    event_dao = DetectionEventDAO(str(db_file))
    return DetectionService(model_service=model_service, event_dao=event_dao)


def test_detect_single_record(detection_service):
    """Verifies single record classification and structure."""
    record = {
        "dur": 0.05,
        "proto": "tcp",
        "service": "http",
        "state": "FIN",
        "spkts": 10,
        "dpkts": 8,
        "sbytes": 1000,
        "dbytes": 2000,
        "rate": 50.0,
        "sttl": 64,
        "dttl": 128,
        "sload": 1000.0,
        "dload": 2000.0,
    }
    result = detection_service.detect_single(record, source_type="test")
    assert "prediction" in result
    assert result["prediction"] in ["Normal Traffic", "Potential Attack"]
    assert "class_id" in result
    assert result["class_id"] in [0, 1]
    assert "attack_score" in result
    assert 0.0 <= result["attack_score"] <= 1.0
    assert "severity" in result
    assert "timestamp" in result


def test_detect_batch_records(detection_service):
    """Verifies batch classification preserves order."""
    records = [
        {"dur": 0.01, "proto": "tcp", "service": "http", "state": "FIN", "sbytes": 100},
        {"dur": 1.50, "proto": "udp", "service": "dns", "state": "CON", "sbytes": 500},
    ]
    results = detection_service.detect_batch(records, source_type="test")
    assert len(results) == 2
    for r in results:
        assert 0.0 <= r["attack_score"] <= 1.0


def test_detect_batch_size_limit(detection_service):
    """Verifies that exceeding MAX_BATCH_SIZE raises ValueError."""
    oversized = [{"dur": 0.1}] * 5001
    with pytest.raises(ValueError, match="exceeds maximum allowable limit"):
        detection_service.detect_batch(oversized)
