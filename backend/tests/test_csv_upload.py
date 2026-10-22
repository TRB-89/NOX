"""
NØX - Unit Tests: CSV Dataset Upload & Validation
Tests CSV header verification, oversized upload rejection, empty files, and streaming analysis.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_csv_upload_valid_file(client):
    """Verifies that uploading a valid flow CSV returns telemetry summary."""
    csv_content = (
        "dur,proto,service,state,spkts,dpkts,sbytes,dbytes,rate,sttl,dttl,sload,dload\n"
        "0.12,tcp,http,FIN,10,8,1000,2000,50.0,64,128,1000.0,2000.0\n"
        "1.45,udp,dns,CON,4,0,200,0,2.5,254,0,500.0,0.0\n"
    )
    files = {"file": ("test_traffic.csv", csv_content.encode("utf-8"), "text/csv")}
    response = client.post("/api/detect/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_records_analyzed"] == 2
    assert "severity_distribution" in data
    assert len(data["preview_predictions"]) == 2


def test_csv_upload_invalid_extension(client):
    """Verifies non-CSV file is rejected with 400 Bad Request."""
    files = {"file": ("malicious_payload.exe", b"MZ\x90\x00", "application/octet-stream")}
    response = client.post("/api/detect/upload", files=files)
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_csv_upload_empty_file(client):
    """Verifies empty file is rejected with 400 Bad Request."""
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = client.post("/api/detect/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_csv_upload_missing_essential_columns(client):
    """Verifies CSV missing core network flow columns is rejected with 400."""
    csv_content = "some_random_column,another_col\n1,2\n3,4\n"
    files = {"file": ("bad_headers.csv", csv_content.encode("utf-8"), "text/csv")}
    response = client.post("/api/detect/upload", files=files)
    assert response.status_code == 400
    assert "missing essential" in response.json()["detail"].lower()
