"""
NØX - Neural Network Intrusion Detection System
Module 01: Preprocessing Pipeline Orchestrator

Integrates DataLoader, DataCleaner, and FeatureEncoder into an end-to-end reproducible
pipeline. Manages stratified splitting (80% train / 20% val), preserves official test split,
saves all neural-ready arrays, serializes the transformation pipeline with joblib,
and exports feature names and dataset metadata.
"""

import sys
from pathlib import Path

# Add project root to sys.path so backend modules can be imported directly
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import json
import logging
from typing import Optional, Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from backend.preprocessing.data_loader import DataLoader
from backend.preprocessing.data_cleaner import DataCleaner
from backend.preprocessing.feature_encoder import FeatureEncoder

logger = logging.getLogger("NOX.Pipeline")


class PreprocessingPipeline:
    """
    End-to-end preprocessing pipeline for UNSW-NB15 intrusion detection dataset.
    """

    def __init__(
        self,
        raw_data_dir: Optional[Path | str] = None,
        processed_data_dir: Optional[Path | str] = None,
        random_state: int = 42,
        val_size: float = 0.20,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.raw_data_dir = Path(raw_data_dir) if raw_data_dir else base_dir / "data" / "raw"
        self.processed_data_dir = Path(processed_data_dir) if processed_data_dir else base_dir / "data" / "processed"
        self.random_state = random_state
        self.val_size = val_size

        self.data_loader = DataLoader(raw_data_dir=self.raw_data_dir)
        self.cleaner = DataCleaner()
        self.encoder: Optional[FeatureEncoder] = None
        self.is_fitted: bool = False
        self.summary: Dict[str, Any] = {}

    def run(self, save_artifacts: bool = True) -> Dict[str, Any]:
        """
        Executes complete preprocessing sequence:
        1. Loads raw CSV files.
        2. Validates schema and displays dataset metrics.
        3. Cleans data and isolates target label and attack_cat metadata.
        4. Splits official training set into 80% train / 20% val (stratified).
        5. Fits scaler and categorical encoder strictly on train split.
        6. Transforms train, val, and official test sets.
        7. Saves all .npy arrays, joblib pipeline, feature_names.json, and summary.json.
        """
        logger.info("=" * 65)
        logger.info("STARTING NØX PREPROCESSING PIPELINE (MODULE 01)")
        logger.info("=" * 65)

        # 1. Load Raw Datasets
        raw_train_df, raw_test_df = self.data_loader.load_raw_datasets(raise_on_missing=True)
        if raw_train_df is None or raw_test_df is None:
            raise RuntimeError("Cannot execute pipeline without raw dataset CSV files.")

        # 2. Schema Validation & Inspection
        train_schema = self.data_loader.validate_schema(raw_train_df, "Raw Training Set")
        test_schema = self.data_loader.validate_schema(raw_test_df, "Raw Testing Set")
        if not train_schema["is_schema_valid"] or not test_schema["is_schema_valid"]:
            logger.warning("One or more schema validations reported missing columns.")

        train_inspection = self.data_loader.inspect_dataset(raw_train_df, "Raw Training Set")
        test_inspection = self.data_loader.inspect_dataset(raw_test_df, "Raw Testing Set")

        # 3. Clean Data & Extract Targets
        # Fit cleaner on raw training data to establish baseline imputation medians/modes
        self.cleaner.fit(raw_train_df)
        X_train_full, y_train_full, cat_train_full = self.cleaner.transform(
            raw_train_df, dataset_name="Train-Full", drop_invalid_targets=True
        )
        X_test_clean, y_test_clean, cat_test_clean = self.cleaner.transform(
            raw_test_df, dataset_name="Test-Official", drop_invalid_targets=True
        )

        # 4. Stratified Split (80% Train, 20% Val)
        logger.info(
            "Performing stratified split on official training set (val_size=%.2f, random_state=%d)...",
            self.val_size,
            self.random_state,
        )

        indices = np.arange(len(X_train_full))
        train_idx, val_idx = train_test_split(
            indices,
            test_size=self.val_size,
            random_state=self.random_state,
            stratify=y_train_full,
        )

        X_train_df = X_train_full.iloc[train_idx].reset_index(drop=True)
        y_train_s = y_train_full.iloc[train_idx].reset_index(drop=True)
        cat_train_s = cat_train_full.iloc[train_idx].reset_index(drop=True) if cat_train_full is not None else None

        X_val_df = X_train_full.iloc[val_idx].reset_index(drop=True)
        y_val_s = y_train_full.iloc[val_idx].reset_index(drop=True)
        cat_val_s = cat_train_full.iloc[val_idx].reset_index(drop=True) if cat_train_full is not None else None

        # 5. Fit FeatureEncoder strictly on X_train_df
        self.encoder = FeatureEncoder(
            numeric_cols=self.cleaner.numeric_cols,
            categorical_cols=self.cleaner.categorical_cols,
        )
        self.encoder.fit(X_train_df)
        self.is_fitted = True

        # 6. Transform Features
        X_train = self.encoder.transform(X_train_df, dataset_name="Train")
        X_val = self.encoder.transform(X_val_df, dataset_name="Validation")
        X_test = self.encoder.transform(X_test_clean, dataset_name="Test-Official")

        y_train = y_train_s.to_numpy(dtype=np.int64)
        y_val = y_val_s.to_numpy(dtype=np.int64)
        y_test = y_test_clean.to_numpy(dtype=np.int64)

        cat_train = cat_train_s.to_numpy(dtype=str) if cat_train_s is not None else np.array([])
        cat_val = cat_val_s.to_numpy(dtype=str) if cat_val_s is not None else np.array([])
        cat_test = cat_test_clean.to_numpy(dtype=str) if cat_test_clean is not None else np.array([])

        feature_names = self.encoder.get_feature_names()

        # Build Summary Metadata
        self.summary = self._build_summary(
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            y_val=y_val,
            y_test=y_test,
            cat_train=cat_train,
            cat_val=cat_val,
            cat_test=cat_test,
            feature_names=feature_names,
            train_inspection=train_inspection,
            test_inspection=test_inspection,
        )

        # 7. Save Artifacts
        if save_artifacts:
            self.save_processed_data(
                X_train=X_train,
                X_val=X_val,
                X_test=X_test,
                y_train=y_train,
                y_val=y_val,
                y_test=y_test,
                cat_train=cat_train,
                cat_val=cat_val,
                cat_test=cat_test,
                feature_names=feature_names,
                summary=self.summary,
            )

        logger.info("=" * 65)
        logger.info("NØX PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 65)
        return self.summary

    def _build_summary(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_val: np.ndarray,
        y_test: np.ndarray,
        cat_train: np.ndarray,
        cat_val: np.ndarray,
        cat_test: np.ndarray,
        feature_names: list[str],
        train_inspection: dict,
        test_inspection: dict,
    ) -> Dict[str, Any]:
        """Compiles detailed dataset summary for json export."""

        def get_binary_stats(y: np.ndarray) -> dict:
            normal = int((y == 0).sum())
            malicious = int((y == 1).sum())
            total = len(y)
            return {
                "total": total,
                "normal_count": normal,
                "normal_percentage": round((normal / total) * 100, 2) if total else 0,
                "malicious_count": malicious,
                "malicious_percentage": round((malicious / total) * 100, 2) if total else 0,
            }

        def get_cat_stats(cats: np.ndarray) -> dict:
            if len(cats) == 0:
                return {}
            unique, counts = np.unique(cats, return_counts=True)
            total = len(cats)
            return {
                str(u): {"count": int(c), "percentage": round((c / total) * 100, 2)}
                for u, c in sorted(zip(unique, counts), key=lambda x: x[1], reverse=True)
            }

        summary = {
            "project": "NØX — Neural Network Intrusion Detection System",
            "module": "Module 01: Dataset Integration & Preprocessing",
            "random_seed": self.random_state,
            "validation_split_ratio": self.val_size,
            "raw_dataset_source": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
            "dataset_sizes": {
                "train_records": int(X_train.shape[0]),
                "validation_records": int(X_val.shape[0]),
                "test_records": int(X_test.shape[0]),
                "total_records_ingested": int(X_train.shape[0] + X_val.shape[0] + X_test.shape[0]),
            },
            "feature_counts": {
                "raw_input_columns": 45,
                "excluded_identifier_columns": self.cleaner.drop_cols,
                "excluded_target_columns": [self.cleaner.target_col],
                "excluded_metadata_columns": self.cleaner.metadata_cols,
                "raw_numeric_features": len(self.cleaner.numeric_cols),
                "raw_categorical_features": len(self.cleaner.categorical_cols),
                "processed_neural_features": int(X_train.shape[1]),
            },
            "categorical_features_encoded": self.cleaner.categorical_cols,
            "numerical_features_scaled": self.cleaner.numeric_cols,
            "class_distribution": {
                "training_set": get_binary_stats(y_train),
                "validation_set": get_binary_stats(y_val),
                "testing_set": get_binary_stats(y_test),
            },
            "attack_categories_distribution": {
                "training_set": get_cat_stats(cat_train),
                "validation_set": get_cat_stats(cat_val),
                "testing_set": get_cat_stats(cat_test),
            },
            "data_cleaning_metrics": self.cleaner.cleaning_stats,
            "data_hygiene_assertions": {
                "train_nan_free": bool(not np.isnan(X_train).any()),
                "val_nan_free": bool(not np.isnan(X_val).any()),
                "test_nan_free": bool(not np.isnan(X_test).any()),
                "train_finite_only": bool(np.isfinite(X_train).all()),
                "val_finite_only": bool(np.isfinite(X_val).all()),
                "test_finite_only": bool(np.isfinite(X_test).all()),
            },
        }
        return summary

    def save_processed_data(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_val: np.ndarray,
        y_test: np.ndarray,
        cat_train: np.ndarray,
        cat_val: np.ndarray,
        cat_test: np.ndarray,
        feature_names: list[str],
        summary: dict,
    ) -> None:
        """Saves all processed arrays and transformation pipeline."""
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Saving processed datasets to: %s", self.processed_data_dir)

        # 1. Feature Arrays
        np.save(self.processed_data_dir / "X_train.npy", X_train)
        np.save(self.processed_data_dir / "X_val.npy", X_val)
        np.save(self.processed_data_dir / "X_test.npy", X_test)

        # 2. Target Labels
        np.save(self.processed_data_dir / "y_train.npy", y_train)
        np.save(self.processed_data_dir / "y_val.npy", y_val)
        np.save(self.processed_data_dir / "y_test.npy", y_test)

        # 3. Metadata Attack Categories (for future multi-class analysis)
        np.save(self.processed_data_dir / "attack_cat_train.npy", cat_train)
        np.save(self.processed_data_dir / "attack_cat_val.npy", cat_val)
        np.save(self.processed_data_dir / "attack_cat_test.npy", cat_test)

        # 4. Feature Names JSON
        feature_names_path = self.processed_data_dir / "feature_names.json"
        with open(feature_names_path, "w", encoding="utf-8") as f:
            json.dump(feature_names, f, indent=2)

        # 5. Dataset Summary JSON
        summary_path = self.processed_data_dir / "dataset_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # 6. Serialized Pipeline
        pipeline_artifacts = {
            "cleaner": self.cleaner,
            "encoder": self.encoder,
            "feature_names": feature_names,
            "version": "1.0.0",
        }
        pipeline_path = self.processed_data_dir / "preprocessing_pipeline.joblib"
        joblib.dump(pipeline_artifacts, pipeline_path)

        logger.info("All processed artifacts successfully exported to %s", self.processed_data_dir)

    def transform_inference(self, raw_df: pd.DataFrame) -> np.ndarray:
        """
        Transforms un-preprocessed network traffic rows for future real-time inference.
        Uses the exact fitted cleaner and encoder.
        """
        if not self.is_fitted or self.encoder is None:
            raise RuntimeError("Pipeline must be fitted or loaded before inference transformation.")

        X_clean, _, _ = self.cleaner.transform(raw_df, dataset_name="Inference", drop_invalid_targets=False)
        X_encoded = self.encoder.transform(X_clean, dataset_name="Inference")
        return X_encoded

    @classmethod
    def load_pipeline(cls, pipeline_joblib_path: Path | str) -> "PreprocessingPipeline":
        """
        Loads a serialized pipeline for standalone inference or testing.
        """
        pipeline_joblib_path = Path(pipeline_joblib_path)
        if not pipeline_joblib_path.exists():
            raise FileNotFoundError(f"Pipeline artifact not found at {pipeline_joblib_path}")

        artifacts = joblib.load(pipeline_joblib_path)
        instance = cls()
        instance.cleaner = artifacts["cleaner"]
        instance.encoder = artifacts["encoder"]
        instance.is_fitted = True
        return instance


if __name__ == "__main__":
    pipeline = PreprocessingPipeline()
    summary = pipeline.run(save_artifacts=True)
    print("\n[+] Preprocessing Complete. Output summary:")
    print(json.dumps(summary["dataset_sizes"], indent=2))
    print(f"Total neural input features: {summary['feature_counts']['processed_neural_features']}")
