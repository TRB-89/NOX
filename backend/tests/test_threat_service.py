"""
NØX - Unit Tests: Threat Severity Service
Tests classification rules across Normal, Low, Medium, and High tiers.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.services.threat_service import ThreatService


def test_threat_severity_normal():
    """Scores below threshold must always map to Normal severity."""
    assert ThreatService.classify_severity(0.10, threshold=0.50) == "Normal"
    assert ThreatService.classify_severity(0.49, threshold=0.50) == "Normal"
    assert ThreatService.classify_severity(0.00, threshold=0.50) == "Normal"


def test_threat_severity_low():
    """Scores at or just above threshold map to Low severity."""
    assert ThreatService.classify_severity(0.51, threshold=0.50) == "Low"
    assert ThreatService.classify_severity(0.65, threshold=0.50) == "Low"


def test_threat_severity_medium():
    """Scores in intermediate range map to Medium severity."""
    assert ThreatService.classify_severity(0.75, threshold=0.50) == "Medium"
    assert ThreatService.classify_severity(0.85, threshold=0.50) == "Medium"


def test_threat_severity_high():
    """Scores at or above 0.90 map to High severity."""
    assert ThreatService.classify_severity(0.90, threshold=0.50) == "High"
    assert ThreatService.classify_severity(0.99, threshold=0.50) == "High"
    assert ThreatService.classify_severity(1.00, threshold=0.50) == "High"


def test_threat_service_enrich_detection():
    """Verifies that enrich_detection appends the severity key."""
    pred = {"attack_score": 0.94, "threshold": 0.50}
    enriched = ThreatService.enrich_detection(pred)
    assert "severity" in enriched
    assert enriched["severity"] == "High"
