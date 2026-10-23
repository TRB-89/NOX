"""
NØX - Integration Tests: FastAPI Application
Tests health check, single detection endpoint, batch detection, history, and stats.
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


def test_root_endpoint(client):
    """Verifies API root response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data
    assert data["documentation"] == "/docs"


def test_health_endpoint(client):
    """Verifies that both /api/health and /health report ready and loaded model."""
    for path in ["/api/health", "/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["model_loaded"] is True
        assert "NØX-MLP" in data["model_version"]

    # Verify lightweight HEAD check
    head_resp = client.head("/health")
    assert head_resp.status_code == 200


def test_detect_endpoint_single(client):
    """Verifies POST /api/detect with a single flow record."""
    payload = {
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
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal Traffic", "Potential Attack"]
    assert data["class_id"] in [0, 1]
    assert 0.0 <= data["attack_score"] <= 1.0
    assert data["severity"] in ["Normal", "Low", "Medium", "High"]
    assert "timestamp" in data


def test_detect_endpoint_batch(client):
    """Verifies POST /api/detect/batch with multiple records."""
    payload = {
        "records": [
            {"dur": 0.01, "proto": "tcp", "service": "http", "state": "FIN"},
            {"dur": 0.50, "proto": "udp", "service": "dns", "state": "CON"},
        ]
    }
    response = client.post("/api/detect/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_history_endpoint(client):
    """Verifies GET /api/history returns logged events."""
    response = client.get("/api/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_stats_endpoint(client):
    """Verifies GET /api/stats returns dashboard telemetry metrics."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_records_analyzed" in data
    assert "predicted_normal_count" in data
    assert "predicted_malicious_count" in data
    assert "severity_distribution" in data


def test_cors_preflight_vercel_origin(client):
    """Verifies that CORS properly permits Vercel domain origins."""
    headers = {
        "Origin": "https://nox-neural-ids.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/detect", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://nox-neural-ids.vercel.app"


def test_cors_preflight_health_endpoint(client):
    """Verifies CORS preflight on root /health and /api/health for Vercel preview deployments."""
    headers = {
        "Origin": "https://nox-preview-xyz123.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type",
    }
    for path in ["/api/health", "/health"]:
        response = client.options(path, headers=headers)
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://nox-preview-xyz123.vercel.app"

