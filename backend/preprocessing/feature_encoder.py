"""
NØX - Neural Network Intrusion Detection System
Module 01: Feature Encoder & Scaler

Combines numerical normalization (StandardScaler) and categorical one-hot encoding
(OneHotEncoder with handle_unknown="ignore") inside a scikit-learn ColumnTransformer.
Guarantees consistent feature alignment, strict training-only fitting, and finite outputs.
"""

import logging
from typing import List, Optional, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger("NOX.FeatureEncoder")


class FeatureEncoder:
    """
    Orchestrates scikit-learn ColumnTransformer for numerical scaling and categorical encoding.
    Ensures identical feature ordering across training, validation, and testing sets.
    """

    def __init__(
        self,
        numeric_cols: Optional[List[str]] = None,
        categorical_cols: Optional[List[str]] = None,
    ):
        self.numeric_cols = list(numeric_cols) if numeric_cols is not None else []
        self.categorical_cols = list(categorical_cols) if categorical_cols is not None else []
        self.transformer: Optional[ColumnTransformer] = None
        self.is_fitted: bool = False
        self.feature_names_out: List[str] = []
        self.total_transformed_features: int = 0

    def _build_column_transformer(self) -> ColumnTransformer:
        """
        Constructs the unified ColumnTransformer:
        - StandardScaler for numerical continuous features
        - OneHotEncoder(handle_unknown='ignore', sparse_output=False) for discrete protocols/states
        """
        # scikit-learn 1.2+ uses sparse_output instead of sparse
        ohe = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float32,
        )
        scaler = StandardScaler()

        transformers = []
        if self.numeric_cols:
            transformers.append(("num_scaler", scaler, self.numeric_cols))
        if self.categorical_cols:
            transformers.append(("cat_encoder", ohe, self.categorical_cols))

        ct = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            verbose_feature_names_out=False,
        )
        return ct

    def fit(self, X_train: pd.DataFrame) -> "FeatureEncoder":
        """
        Fits the ColumnTransformer strictly on the training partition.
        Never call this on validation or testing data.
        """
        logger.info("Fitting FeatureEncoder (StandardScaler + OneHotEncoder) on training data...")

        # If columns weren't manually provided, auto-discover from X_train
        if not self.numeric_cols and not self.categorical_cols:
            self.categorical_cols = list(X_train.select_dtypes(include=["object", "string", "category"]).columns)
            self.numeric_cols = [c for c in X_train.columns if c not in self.categorical_cols]

        self.transformer = self._build_column_transformer()
        self.transformer.fit(X_train)

        # Extract output feature names
        try:
            self.feature_names_out = list(self.transformer.get_feature_names_out())
        except Exception:
            # Fallback if names resolution is unavailable
            self.feature_names_out = [f"f_{i}" for i in range(self.transformer.transform(X_train.iloc[:2]).shape[1])]

        self.total_transformed_features = len(self.feature_names_out)
        self.is_fitted = True

        logger.info(
            "FeatureEncoder successfully fitted. Total output neural features: %d",
            self.total_transformed_features,
        )
        return self

    def transform(self, X: pd.DataFrame, dataset_name: str = "Dataset") -> np.ndarray:
        """
        Transforms input features X into a dense, scaled, normalized numerical numpy array.
        Performs sanity checks to guarantee zero NaN or infinite values.
        """
        if not self.is_fitted or self.transformer is None:
            raise RuntimeError("FeatureEncoder must be fitted on training data before calling transform()!")

        transformed_matrix = self.transformer.transform(X)

        # Convert to float32 for deep learning efficiency
        if not isinstance(transformed_matrix, np.ndarray):
            transformed_matrix = transformed_matrix.toarray()
        transformed_matrix = transformed_matrix.astype(np.float32)

        # Assert no NaN or infinite values remain
        has_nan = bool(np.isnan(transformed_matrix).any())
        has_inf = bool(np.isinf(transformed_matrix).any())

        if has_nan or has_inf:
            raise ValueError(
                f"[{dataset_name}] Post-transformation matrix contains invalid values! "
                f"NaN detected: {has_nan}, Inf detected: {has_inf}"
            )

        logger.info(
            "[%s] Transformed feature array shape: %s (finite, float32)",
            dataset_name,
            transformed_matrix.shape,
        )
        return transformed_matrix

    def fit_transform(self, X_train: pd.DataFrame, dataset_name: str = "Training") -> np.ndarray:
        """Fits on training data and transforms."""
        return self.fit(X_train).transform(X_train, dataset_name=dataset_name)

    def get_feature_names(self) -> List[str]:
        """Returns the list of final transformed feature names."""
        if not self.is_fitted:
            raise RuntimeError("Encoder has not been fitted yet.")
        return self.feature_names_out
