"""
NØX - Neural Network Intrusion Detection System
Module 02: Multilayer Perceptron (MLP) Architecture

A PyTorch neural network for binary intrusion detection (Normal vs Potential Attack)
operating on preprocessed, scaled, and one-hot encoded UNSW-NB15 flow features.
"""

from typing import Dict, Any, Optional
import torch
import torch.nn as nn


class NoxMLP(nn.Module):
    """
    Multilayer Perceptron for network traffic intrusion classification.

    Architecture:
        Input Layer (dynamic input_dim)
            ↓
        Linear(input_dim, 128)
            ↓
        ReLU()
            ↓
        Dropout(p=0.3)
            ↓
        Linear(128, 64)
            ↓
        ReLU()
            ↓
        Dropout(p=0.2)
            ↓
        Linear(64, 1)
            ↓
        Raw Logit (Binary Classification)
    """

    CLASS_NAMES = {
        0: "Normal Network Traffic",
        1: "Potential Malicious Network Traffic",
    }

    def __init__(self, input_dim: int, dropout_1: float = 0.3, dropout_2: float = 0.2):
        super(NoxMLP, self).__init__()

        if input_dim <= 0:
            raise ValueError(f"input_dim must be positive, got {input_dim}")

        self.input_dim = input_dim
        self.dropout_1_rate = dropout_1
        self.dropout_2_rate = dropout_2

        # Fully connected layers with dropout regularization
        self.layer1 = nn.Linear(input_dim, 128)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(p=dropout_1)

        self.layer2 = nn.Linear(128, 64)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(p=dropout_2)

        self.out_layer = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass returning raw unactivated logits.
        BCEWithLogitsLoss combines sigmoid internally for numerical stability during training.
        """
        x = self.layer1(x)
        x = self.relu1(x)
        x = self.dropout1(x)

        x = self.layer2(x)
        x = self.relu2(x)
        x = self.dropout2(x)

        logits = self.out_layer(x)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """
        Applies sigmoid to logits to yield calibrated attack probabilities in [0.0, 1.0].
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = torch.sigmoid(logits)
        return probabilities

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Returns architecture metadata for tracking and serialization."""
        return {
            "model_type": "Multilayer Perceptron (MLP)",
            "input_dim": self.input_dim,
            "hidden_layers": [
                {"layer": "Linear(input_dim, 128)", "activation": "ReLU", "dropout": self.dropout_1_rate},
                {"layer": "Linear(128, 64)", "activation": "ReLU", "dropout": self.dropout_2_rate},
                {"layer": "Linear(64, 1)", "output": "Binary Logit"},
            ],
            "total_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad),
            "classes": self.CLASS_NAMES,
        }


def get_default_device() -> torch.device:
    """
    Selects CUDA GPU acceleration if available, otherwise defaults gracefully to CPU.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")
