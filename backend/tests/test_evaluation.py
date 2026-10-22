"""
NØX - Unit Tests: Model Evaluation Module
Tests metric computation, confusion matrix consistency,
ROC-AUC generation, and evaluation JSON artifact structure.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
import numpy as np
from backend.training.evaluate import ModelEvaluator


@pytest.fixture(scope="module")
def evaluator():
    return ModelEvaluator()


def test_evaluate_predictions_metrics(evaluator):
    """Verifies standard evaluation metric calculations."""
    y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    y_probs = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.3, 0.7, 0.6])
    threshold = 0.50

    metrics = evaluator.evaluate_predictions(y_true, y_probs, threshold)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "false_positive_rate" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics

    cm = metrics["confusion_matrix"]
    total_cm = cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"]
    assert total_cm == len(y_true)

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert 0.0 <= metrics["false_positive_rate"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0


def test_evaluation_json_artifact_exists():
    """Verifies that evaluation_results.json exists and contains complete benchmarking."""
    base_dir = Path(__file__).resolve().parent.parent
    eval_json = base_dir / "outputs" / "metrics" / "evaluation_results.json"

    if not eval_json.exists():
        pytest.skip("evaluation_results.json has not been generated yet.")

    import json
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "mlp_model_performance" in data
    assert "logistic_regression_baseline_performance" in data
    assert "comparison_summary" in data
    assert data["test_sample_count"] == 82332
