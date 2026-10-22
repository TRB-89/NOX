"""
NØX - Neural Network Intrusion Detection System
Module 01: Data Cleaner

Performs data hygiene, handles invalid values and infinities, reports duplicate flows,
strictly isolates target labels and metadata, and imputes missing values using
statistics derived exclusively from training data.
"""

from pathlib import Path
import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, List, Any

logger = logging.getLogger("NOX.DataCleaner")

DEFAULT_DROP_COLUMNS = ["id"]
DEFAULT_TARGET_COLUMN = "label"
DEFAULT_METADATA_COLUMNS = ["attack_cat"]
DEFAULT_CATEGORICAL_COLUMNS = ["proto", "service", "state"]


class DataCleaner:
    """
    Cleans raw network traffic frames, eliminates target leakage, validates labels,
    and applies training-derived statistical imputation without data leakage.
    """

    def __init__(
        self,
        drop_cols: Optional[List[str]] = None,
        target_col: str = DEFAULT_TARGET_COLUMN,
        metadata_cols: Optional[List[str]] = None,
        categorical_cols: Optional[List[str]] = None,
    ):
        self.drop_cols = drop_cols if drop_cols is not None else list(DEFAULT_DROP_COLUMNS)
        self.target_col = target_col
        self.metadata_cols = metadata_cols if metadata_cols is not None else list(DEFAULT_METADATA_COLUMNS)
        self.categorical_cols = categorical_cols if categorical_cols is not None else list(DEFAULT_CATEGORICAL_COLUMNS)

        self.numeric_cols: List[str] = []
        self.numeric_medians: Dict[str, float] = {}
        self.categorical_modes: Dict[str, str] = {}
        self.is_fitted: bool = False
        self.cleaning_stats: Dict[str, Any] = {}

    def report_duplicates(self, df: pd.DataFrame, stage_name: str = "Dataset") -> Dict[str, int]:
        """
        Detects and logs duplicate network flow records.
        Reports duplicates both with identifier ('id') and without identifier.
        """
        total_rows = len(df)
        dup_with_id = int(df.duplicated().sum())

        cols_excluding_id = [c for c in df.columns if c not in self.drop_cols]
        dup_without_id = int(df.duplicated(subset=cols_excluding_id).sum()) if cols_excluding_id else 0

        logger.info(
            "[%s] Total records: %d | Duplicates (with ID): %d | Duplicates (flow features excluding ID): %d",
            stage_name,
            total_rows,
            dup_with_id,
            dup_without_id,
        )
        return {
            "total_records": total_rows,
            "duplicates_with_id": dup_with_id,
            "duplicates_feature_flows": dup_without_id,
        }

    def _sanitize_infinities_and_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Replaces +/- infinity with NaN in all numeric columns and strips string fields.
        """
        df_clean = df.copy()

        # Strip whitespace in string/object columns
        for col in df_clean.select_dtypes(include=["object", "string"]).columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

        # Handle numeric infinity
        num_cols = df_clean.select_dtypes(include=[np.number]).columns
        inf_mask = np.isinf(df_clean[num_cols])
        inf_count = int(inf_mask.sum().sum())
        if inf_count > 0:
            logger.warning("Found %d infinite values; replacing with NaN for imputation.", inf_count)
            df_clean[num_cols] = df_clean[num_cols].replace([np.inf, -np.inf], np.nan)

        return df_clean

    def fit(self, df: pd.DataFrame) -> "DataCleaner":
        """
        Computes imputation statistics strictly on training data.
        Determines numerical and categorical feature rosters.
        """
        logger.info("Fitting DataCleaner on training data...")
        df_clean = self._sanitize_infinities_and_types(df)

        # Remove rows with invalid target labels during fitting if target present
        if self.target_col in df_clean.columns:
            valid_mask = df_clean[self.target_col].isin([0, 1]) & df_clean[self.target_col].notnull()
            df_clean = df_clean[valid_mask]

        # Determine feature columns (exclude drops, target, and metadata)
        excluded = set(self.drop_cols + [self.target_col] + self.metadata_cols)
        available_cols = [c for c in df_clean.columns if c not in excluded]

        # Identify categorical columns
        cat_cols = [c for c in self.categorical_cols if c in available_cols]
        for c in available_cols:
            if df_clean[c].dtype == "object" or df_clean[c].dtype.name == "string":
                if c not in cat_cols:
                    cat_cols.append(c)

        # Identify numeric columns
        num_cols = [c for c in available_cols if c not in cat_cols]

        self.categorical_cols = cat_cols
        self.numeric_cols = num_cols

        # Compute medians for numerical columns
        self.numeric_medians = {}
        for col in self.numeric_cols:
            med = df_clean[col].median()
            self.numeric_medians[col] = 0.0 if pd.isna(med) else float(med)

        # Compute modes for categorical columns
        self.categorical_modes = {}
        for col in self.categorical_cols:
            mode_series = df_clean[col].mode()
            self.categorical_modes[col] = str(mode_series.iloc[0]) if not mode_series.empty else "unknown"

        self.is_fitted = True
        logger.info(
            "DataCleaner fitted successfully: %d numerical features, %d categorical features.",
            len(self.numeric_cols),
            len(self.categorical_cols),
        )
        return self

    def transform(
        self,
        df: pd.DataFrame,
        dataset_name: str = "Dataset",
        drop_invalid_targets: bool = True,
    ) -> Tuple[pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
        """
        Transforms dataset into clean feature matrix X, binary target y, and metadata attack_cat.
        Uses previously fitted training statistics for imputation to prevent data leakage.
        """
        if not self.is_fitted:
            raise RuntimeError("DataCleaner must be fitted on training data before calling transform()!")

        df_work = self._sanitize_infinities_and_types(df)

        # Record duplicate statistics
        dup_stats = self.report_duplicates(df_work, stage_name=dataset_name)
        self.cleaning_stats[f"{dataset_name}_duplicates"] = dup_stats

        # Validate target labels if present
        y: Optional[pd.Series] = None
        if self.target_col in df_work.columns:
            if drop_invalid_targets:
                valid_mask = df_work[self.target_col].isin([0, 1]) & df_work[self.target_col].notnull()
                dropped_targets = int((~valid_mask).sum())
                if dropped_targets > 0:
                    logger.warning(
                        "[%s] Dropped %d rows due to invalid/missing target labels.",
                        dataset_name,
                        dropped_targets,
                    )
                df_work = df_work[valid_mask]
            y = df_work[self.target_col].astype(int)

        # Extract metadata (attack_cat) if present
        metadata: Optional[pd.Series] = None
        for meta_col in self.metadata_cols:
            if meta_col in df_work.columns:
                metadata = df_work[meta_col].fillna("Normal").astype(str).str.strip()
                break

        # Assemble input feature matrix X strictly excluding drop_cols, target_col, metadata_cols
        feature_columns = self.numeric_cols + self.categorical_cols
        missing_in_input = [col for col in feature_columns if col not in df_work.columns]
        if missing_in_input:
            # Impute omitted features using training statistics
            for col in missing_in_input:
                if col in self.numeric_medians:
                    df_work[col] = self.numeric_medians[col]
                elif col in self.categorical_modes:
                    df_work[col] = self.categorical_modes[col]
                else:
                    df_work[col] = 0.0

        X = df_work[feature_columns].copy()

        # Apply training-derived statistical imputation
        # 1. Numeric imputation
        for col in self.numeric_cols:
            if X[col].isnull().any():
                impute_val = self.numeric_medians[col]
                X[col] = X[col].fillna(impute_val)
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(self.numeric_medians[col])

        # 2. Categorical imputation
        for col in self.categorical_cols:
            if X[col].isnull().any() or (X[col] == "").any():
                impute_val = self.categorical_modes[col]
                X[col] = X[col].replace("", impute_val).fillna(impute_val)
            X[col] = X[col].astype(str)

        # Double check no leakage
        leakage = [col for col in self.drop_cols + [self.target_col] + self.metadata_cols if col in X.columns]
        if leakage:
            raise ValueError(f"CRITICAL TARGET LEAKAGE: Columns {leakage} detected in feature matrix X!")

        logger.info(
            "[%s] Cleaned X shape: %s | y shape: %s | metadata shape: %s",
            dataset_name,
            X.shape,
            y.shape if y is not None else None,
            metadata.shape if metadata is not None else None,
        )
        return X, y, metadata

    def fit_transform(
        self,
        df: pd.DataFrame,
        dataset_name: str = "Training",
    ) -> Tuple[pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
        """Fits on training data and transforms."""
        return self.fit(df).transform(df, dataset_name=dataset_name, drop_invalid_targets=True)
