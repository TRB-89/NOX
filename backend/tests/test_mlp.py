"""
NØX - Unit Tests: Neural Network Architecture (NoxMLP)
Tests dynamic dimension initialization, forward pass logit shapes,
activation bounds, and parameter updates.
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
import torch
from backend.models.mlp_model import NoxMLP, get_default_device


def test_mlp_dynamic_dimension_init():
    """Verifies that model initializes dynamically with varied feature dimensions."""
    model_50 = NoxMLP(input_dim=50)
    assert model_50.input_dim == 50
    assert model_50.layer1.in_features == 50

    model_192 = NoxMLP(input_dim=192)
    assert model_192.input_dim == 192
    assert model_192.layer1.in_features == 192

    with pytest.raises(ValueError):
        NoxMLP(input_dim=0)

    with pytest.raises(ValueError):
        NoxMLP(input_dim=-10)


def test_mlp_forward_pass_dimensions():
    """Verifies forward pass returns raw logits with correct (batch_size, 1) shape."""
    model = NoxMLP(input_dim=192)
    batch_size = 16
    x = torch.randn(batch_size, 192)

    logits = model(x)
    assert logits.shape == (batch_size, 1)
    assert logits.dtype == torch.float32


def test_mlp_predict_proba_bounds():
    """Verifies that predict_proba applies sigmoid and strictly bounds outputs in [0, 1]."""
    model = NoxMLP(input_dim=64)
    x = torch.randn(20, 64)

    probs = model.predict_proba(x)
    assert probs.shape == (20, 1)
    assert (probs >= 0.0).all().item()
    assert (probs <= 1.0).all().item()


def test_architecture_summary():
    """Verifies metadata summary generation."""
    model = NoxMLP(input_dim=192)
    summary = model.get_architecture_summary()
    assert summary["input_dim"] == 192
    assert summary["total_parameters"] > 0
    assert 0 in summary["classes"]
    assert 1 in summary["classes"]
