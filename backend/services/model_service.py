"""
NØX - Model Service
Loads and manages trusted local ML artifacts: PyTorch NoxMLP, model metadata,
and the fitted scikit-learn preprocessing pipeline. Executes inference using torch.inference_mode().
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Root resolution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import joblib
import numpy as np
import pandas as pd
import torch

from backend.models.mlp_model import NoxMLP

logger = logging.getLogger("NOX.ModelService")


class ModelService:
    """
    Singleton-capable service for loading trained PyTorch weights and
    Module 01 preprocessing pipeline without refitting.
    """

    def __init__(
        self,
        model_weights_path: Optional[Path | str] = None,
        metadata_path: Optional[Path | str] = None,
        pipeline_path: Optional[Path | str] = None,
        device: str = "cpu",
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.model_weights_path = Path(model_weights_path) if model_weights_path else base_dir / "models" / "saved" / "nox_mlp.pth"
        self.metadata_path = Path(metadata_path) if metadata_path else base_dir / "models" / "saved" / "model_metadata.json"
        self.pipeline_path = Path(pipeline_path) if pipeline_path else base_dir / "data" / "processed" / "preprocessing_pipeline.joblib"

        self.device = torch.device(device)
        self.model: Optional[NoxMLP] = None
        self.metadata: Dict[str, Any] = {}
        self.cleaner = None
        self.encoder = None
        self.feature_names: List[str] = []
        self.threshold: float = 0.50
        self.is_loaded: bool = False

    def load_artifacts(self) -> None:
        """
        Loads the trained model weights and preprocessing artifacts from trusted local paths.
        Raises informative errors if required files are missing or corrupted.
        """
        logger.info("Initializing ModelService from local artifacts...")

        # 1. Verify file presence
        for p, desc in [
            (self.model_weights_path, "Model weights (nox_mlp.pth)"),
            (self.metadata_path, "Model metadata (model_metadata.json)"),
            (self.pipeline_path, "Preprocessing pipeline (preprocessing_pipeline.joblib)"),
        ]:
            if not p.exists():
                raise FileNotFoundError(
                    f"Required artifact '{desc}' not found at: {p.resolve()}.\n"
                    "Ensure Module 01 & 02 pipelines have been executed."
                )

        # 2. Load Model Metadata
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            self.threshold = float(self.metadata.get("selected_threshold", 0.50))
            expected_dim = int(self.metadata.get("input_feature_count", 192))
        except Exception as e:
            raise ValueError(f"Corrupted or invalid metadata at {self.metadata_path}: {e}")

        # 3. Load Preprocessing Pipeline
        try:
            pipeline_artifacts = joblib.load(self.pipeline_path)
            self.cleaner = pipeline_artifacts["cleaner"]
            self.encoder = pipeline_artifacts["encoder"]
            self.feature_names = pipeline_artifacts.get("feature_names", [])
        except Exception as e:
            raise ValueError(f"Failed to deserialize preprocessing pipeline at {self.pipeline_path}: {e}")

        # 4. Construct and Load PyTorch Model
        try:
            self.model = NoxMLP(input_dim=expected_dim).to(self.device)
            state_dict = torch.load(self.model_weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to construct and load PyTorch model: {e}")

        self.is_loaded = True
        logger.info(
            "ModelService successfully loaded! Model: %s, Features: %d, Threshold: %.2f, Device: %s",
            self.metadata.get("model_name", "NØX-MLP-v1"),
            expected_dim,
            self.threshold,
            self.device,
        )

    def preprocess_raw_dataframe(self, raw_df: pd.DataFrame) -> np.ndarray:
        """
        Transforms raw network flow dataframe through the fitted cleaner and encoder.
        Guarantees exact 192-dimensional numerical float32 matrix.
        """
        if not self.is_loaded or self.cleaner is None or self.encoder is None:
            raise RuntimeError("ModelService is not loaded. Call load_artifacts() first.")

        # Clean raw features without target labels
        X_clean, _, _ = self.cleaner.transform(raw_df, dataset_name="Inference", drop_invalid_targets=False)
        # One-hot encode and scale features
        X_encoded = self.encoder.transform(X_clean, dataset_name="Inference")
        return X_encoded

    def predict_probabilities(self, X_encoded: np.ndarray) -> np.ndarray:
        """
        Runs neural inference using torch.inference_mode().
        Returns 1D array of calibrated attack scores in [0.0, 1.0].
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("ModelService is not loaded. Call load_artifacts() first.")

        tensor_x = torch.from_numpy(X_encoded).float().to(self.device)
        with torch.inference_mode():
            logits = self.model(tensor_x)
            probabilities = torch.sigmoid(logits).cpu().numpy().flatten()
        return probabilities

    def predict_from_raw(self, raw_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        End-to-end inference from raw dataframe to (scores, binary_predictions).
        """
        X_encoded = self.preprocess_raw_dataframe(raw_df)
        scores = self.predict_probabilities(X_encoded)
        preds = (scores >= self.threshold).astype(int)
        return scores, preds

    def get_info(self) -> Dict[str, Any]:
        """Returns service status and loaded model specifications."""
        return {
            "status": "ready" if self.is_loaded else "uninitialized",
            "model_loaded": self.is_loaded,
            "model_version": self.metadata.get("model_name", "NØX-MLP-v1"),
            "input_feature_count": self.metadata.get("input_feature_count", 192),
            "threshold": self.threshold,
            "device": str(self.device),
        }
