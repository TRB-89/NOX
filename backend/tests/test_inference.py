"""
NØX - Unit Tests: Prediction Engine (NoxPredictor)
Tests single & batch inference, feature dimension validation,
output response schemas, and threshold sensitivity.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
import numpy as np
from backend.inference.predict import NoxPredictor


@pytest.fixture(scope="module")
def predictor():
    """Initializes predictor from saved model."""
    return NoxPredictor()


def test_inference_single_sample_format(predictor):
    """Verifies that single-record inference returns expected JSON structure."""
    dummy_input = np.zeros(predictor.expected_dim, dtype=np.float32)
    result = predictor.predict_single(dummy_input)

    assert "prediction" in result
    assert result["prediction"] in ["Normal Traffic", "Potential Attack"]
    assert "class_id" in result
    assert result["class_id"] in [0, 1]
    assert "attack_score" in result
    assert 0.0 <= result["attack_score"] <= 1.0
    assert "threshold" in result
    assert "model" in result


def test_inference_batch_processing(predictor):
    """Verifies batch inference returns exact number of matching predictions."""
    batch_size = 7
    dummy_batch = np.random.randn(batch_size, predictor.expected_dim).astype(np.float32)
    results = predictor.predict_batch(dummy_batch)

    assert len(results) == batch_size
    for res in results:
        assert 0.0 <= res["attack_score"] <= 1.0
        assert res["prediction"] in ["Normal Traffic", "Potential Attack"]


def test_feature_dimension_validation(predictor):
    """Verifies that predictor raises ValueError when input feature count is wrong."""
    wrong_dim_vector = np.zeros(predictor.expected_dim - 10, dtype=np.float32)

    with pytest.raises(ValueError, match="Feature dimension mismatch"):
        predictor.predict_single(wrong_dim_vector)


def test_threshold_logic(predictor):
    """Verifies custom threshold overrides."""
    high_threshold_pred = NoxPredictor(threshold_override=0.99)
    low_threshold_pred = NoxPredictor(threshold_override=0.01)

    assert high_threshold_pred.threshold == 0.99
    assert low_threshold_pred.threshold == 0.01

    sample = np.zeros(predictor.expected_dim, dtype=np.float32)
    res_high = high_threshold_pred.predict_single(sample)
    res_low = low_threshold_pred.predict_single(sample)

    assert res_high["threshold"] == 0.99
    assert res_low["threshold"] == 0.01
