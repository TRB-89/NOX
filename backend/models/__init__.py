"""
NØX - Neural Network Intrusion Detection System
Models Module
"""

from backend.models.mlp_model import NoxMLP, get_default_device

__all__ = ["NoxMLP", "get_default_device"]
