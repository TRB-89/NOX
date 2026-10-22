"""
NØX - Unit Tests: Training Pipeline Components
Tests loss computation, backpropagation parameter updates,
and model state_dict serialization/deserialization.
"""

import sys
import copy
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
import torch
import torch.nn as nn
from backend.models.mlp_model import NoxMLP


def test_loss_computation_no_errors():
    """Verifies that BCEWithLogitsLoss computes without NaN or inf."""
    criterion = nn.BCEWithLogitsLoss()
    logits = torch.randn(32, 1)
    targets = torch.randint(0, 2, (32, 1)).float()

    loss = criterion(logits, targets)
    assert not torch.isnan(loss)
    assert not torch.isinf(loss)
    assert loss.item() > 0.0


def test_backpropagation_updates_parameters():
    """Verifies that backpropagation updates model weights."""
    model = NoxMLP(input_dim=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.BCEWithLogitsLoss()

    initial_weights = copy.deepcopy(model.layer1.weight.data)

    x = torch.randn(16, 10)
    y = torch.ones(16, 1)

    optimizer.zero_grad()
    logits = model(x)
    loss = criterion(logits, y)
    loss.backward()
    optimizer.step()

    updated_weights = model.layer1.weight.data
    assert not torch.equal(initial_weights, updated_weights), "Weights did not update after step!"


def test_model_saving_and_reloading_consistency(tmp_path):
    """Verifies that saving and reloading state_dict preserves exact predictions."""
    model = NoxMLP(input_dim=20)
    model.eval()

    sample_x = torch.randn(5, 20)
    original_probs = model.predict_proba(sample_x)

    save_path = tmp_path / "test_model.pth"
    torch.save(model.state_dict(), save_path)

    reloaded_model = NoxMLP(input_dim=20)
    reloaded_model.load_state_dict(torch.load(save_path))
    reloaded_model.eval()

    reloaded_probs = reloaded_model.predict_proba(sample_x)
    assert torch.allclose(original_probs, reloaded_probs, atol=1e-6)
