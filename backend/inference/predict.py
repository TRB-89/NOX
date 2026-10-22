"""
NØX - Neural Network Intrusion Detection System
Module 02: Neural Prediction Engine

Reusable inference interface for offline intrusion detection using the trained NoxMLP.
Accepts preprocessed numerical flow vectors, validates feature cardinality, computes
calibrated sigmoid scores, applies frozen threat thresholds, and yields structured results.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

# Root directory resolution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import torch

from backend.models.mlp_model import NoxMLP, get_default_device

logger = logging.getLogger("NOX.Predict")


class NoxPredictor:
    """
    Inference engine for NØX Multilayer Perceptron.
    """

    def __init__(
        self,
        model_path: Optional[Path | str] = None,
        metadata_path: Optional[Path | str] = None,
        threshold_override: Optional[float] = None,
        device: Optional[torch.device] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.model_path = Path(model_path) if model_path else base_dir / "models" / "saved" / "nox_mlp.pth"
        self.metadata_path = Path(metadata_path) if metadata_path else base_dir / "models" / "saved" / "model_metadata.json"
        self.device = device if device else get_default_device()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Trained model checkpoint not found at: {self.model_path.resolve()}.\n"
                "Please run training first: python backend/training/train.py"
            )

        # Load metadata
        self.metadata = self._load_metadata()
        self.model_name = self.metadata.get("model_name", "NØX-MLP-v1")
        self.expected_dim = self.metadata.get("input_feature_count", 192)

        # Set threshold
        if threshold_override is not None:
            self.threshold = float(threshold_override)
        else:
            self.threshold = float(self.metadata.get("selected_threshold", 0.50))

        # Reconstruct and load PyTorch model
        self.model = NoxMLP(input_dim=self.expected_dim).to(self.device)
        state_dict = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

        logger.info(
            "NoxPredictor initialized on device '%s' (Features: %d, Threshold: %.2f)",
            self.device,
            self.expected_dim,
            self.threshold,
        )

    def _load_metadata(self) -> Dict[str, Any]:
        """Loads model metadata JSON if available."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not parse metadata at %s: %s", self.metadata_path, e)
        return {"model_name": "NØX-MLP-v1", "input_feature_count": 192, "selected_threshold": 0.50}

    def _prepare_tensor(self, features: Union[np.ndarray, List[float], List[List[float]], torch.Tensor]) -> torch.Tensor:
        """
        Validates input shape and converts to Float32 2D tensor on target device.
        """
        if isinstance(features, torch.Tensor):
            tensor = features.float()
        elif isinstance(features, (np.ndarray, list)):
            arr = np.array(features, dtype=np.float32)
            tensor = torch.from_numpy(arr)
        else:
            raise TypeError(f"Unsupported features type: {type(features)}")

        # Ensure 2D tensor: [batch_size, num_features]
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        elif tensor.ndim != 2:
            raise ValueError(f"Input must be 1D or 2D tensor/array, got {tensor.ndim} dimensions.")

        batch_size, num_features = tensor.shape
        if num_features != self.expected_dim:
            raise ValueError(
                f"Feature dimension mismatch! Expected {self.expected_dim} preprocessed features, "
                f"but received {num_features}."
            )

        return tensor.to(self.device)

    def predict_single(self, feature_vector: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        """
        Predicts threat probability for a single network flow record.
        Returns formatted JSON dictionary.
        """
        tensor = self._prepare_tensor(feature_vector)
        with torch.no_grad():
            score = float(self.model.predict_proba(tensor).cpu().numpy()[0, 0])

        is_attack = score >= self.threshold
        prediction_label = "Potential Attack" if is_attack else "Normal Traffic"
        class_id = 1 if is_attack else 0

        return {
            "prediction": prediction_label,
            "class_id": class_id,
            "attack_score": round(score, 4),
            "threshold": self.threshold,
            "model": self.model_name,
        }

    def predict_batch(
        self,
        feature_matrix: Union[np.ndarray, List[List[float]], torch.Tensor],
    ) -> List[Dict[str, Any]]:
        """
        Predicts threat probabilities for a batch of network flow records.
        Returns list of structured prediction dictionaries.
        """
        tensor = self._prepare_tensor(feature_matrix)
        with torch.no_grad():
            scores = self.model.predict_proba(tensor).cpu().numpy().flatten()

        results = []
        for s in scores:
            score_val = float(s)
            is_attack = score_val >= self.threshold
            results.append({
                "prediction": "Potential Attack" if is_attack else "Normal Traffic",
                "class_id": 1 if is_attack else 0,
                "attack_score": round(score_val, 4),
                "threshold": self.threshold,
                "model": self.model_name,
            })
        return results


if __name__ == "__main__":
    predictor = NoxPredictor()
    dummy_input = np.zeros((1, predictor.expected_dim), dtype=np.float32)
    sample_res = predictor.predict_single(dummy_input)
    print("\n[+] NoxPredictor Test Inference:")
    print(json.dumps(sample_res, indent=2))
