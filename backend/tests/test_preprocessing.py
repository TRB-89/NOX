"""
NØX - Automated Preprocessing Test Suite
Tests dataset loading, schema validity, isolation against target leakage,
one-hot encoding resilience, training/testing independence, and pipeline serialization.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
import numpy as np
import pandas as pd
import joblib

from backend.preprocessing.data_loader import DataLoader, ESSENTIAL_COLUMNS
from backend.preprocessing.data_cleaner import DataCleaner
from backend.preprocessing.feature_encoder import FeatureEncoder
from backend.preprocessing.pipeline import PreprocessingPipeline

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


@pytest.fixture(scope="session")
def raw_datasets():
    """Session fixture providing raw datasets if present."""
    loader = DataLoader(raw_data_dir=RAW_DIR)
    train_df, test_df = loader.load_raw_datasets(raise_on_missing=False)
    return loader, train_df, test_df


@pytest.fixture
def sample_raw_dataframe():
    """Generates synthetic network flow dataframe reflecting UNSW-NB15 schema."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "dur": [0.12, 1.45, 0.00, np.inf, 0.05],
        "proto": ["tcp", "udp", "tcp", "arp", "unknown_proto"],
        "service": ["http", "-", "dns", "ftp", "-"],
        "state": ["FIN", "INT", "CON", "FIN", "ECO"],
        "spkts": [10, 4, 2, 100, 1],
        "dpkts": [8, 0, 2, 80, 0],
        "sbytes": [1000, 200, 150, 50000, 64],
        "dbytes": [4000, 0, 150, 20000, 0],
        "rate": [50.0, 2.5, 0.0, -np.inf, 10.0],
        "sttl": [64, 254, 31, 64, 254],
        "dttl": [128, 0, 29, 128, 0],
        "sload": [1000.0, 500.0, 200.0, 8000.0, 100.0],
        "dload": [4000.0, 0.0, 200.0, 3000.0, 0.0],
        "attack_cat": ["Normal", "Generic", "Exploits", "DoS", "Normal"],
        "label": [0, 1, 1, 1, 0],
    }
    return pd.DataFrame(data)


# 1. Dataset Loading Tests
def test_csv_file_detection(raw_datasets):
    """Verifies that dataset loader accurately detects raw CSV files."""
    loader, _, _ = raw_datasets
    status = loader.check_files_exist()
    assert "UNSW_NB15_training-set.csv" in status
    assert "UNSW_NB15_testing-set.csv" in status
    # In our environment, both files should exist and be valid
    assert status["UNSW_NB15_training-set.csv"] is True
    assert status["UNSW_NB15_testing-set.csv"] is True


def test_required_columns_exist(raw_datasets):
    """Verifies that all essential UNSW-NB15 benchmark columns are present."""
    loader, train_df, test_df = raw_datasets
    assert train_df is not None, "Training dataframe could not be loaded"
    assert test_df is not None, "Testing dataframe could not be loaded"

    train_schema = loader.validate_schema(train_df, "Train")
    test_schema = loader.validate_schema(test_df, "Test")

    assert train_schema["is_schema_valid"] is True
    assert test_schema["is_schema_valid"] is True
    for col in ESSENTIAL_COLUMNS:
        assert col in train_df.columns, f"Essential column '{col}' missing from training set"
        assert col in test_df.columns, f"Essential column '{col}' missing from testing set"


# 2. Target Label Validity Tests
def test_binary_target_validity(raw_datasets):
    """Verifies that target label contains exclusively 0 and 1."""
    _, train_df, test_df = raw_datasets
    assert set(train_df["label"].unique()).issubset({0, 1})
    assert set(test_df["label"].unique()).issubset({0, 1})
    assert not train_df["label"].isnull().any()
    assert not test_df["label"].isnull().any()


# 3. Target Leakage Prevention Tests
def test_no_target_columns_leak_into_features(sample_raw_dataframe):
    """Verifies that 'id', 'label', and 'attack_cat' are strictly excluded from X."""
    cleaner = DataCleaner()
    X, y, metadata = cleaner.fit_transform(sample_raw_dataframe)

    assert "id" not in X.columns, "CRITICAL: 'id' leaked into model features!"
    assert "label" not in X.columns, "CRITICAL: 'label' leaked into model features!"
    assert "attack_cat" not in X.columns, "CRITICAL: 'attack_cat' leaked into model features!"

    assert y is not None
    assert metadata is not None
    assert len(X) == len(y) == len(metadata)


# 4. Data Hygiene and Imputation Tests
def test_infinities_and_missing_value_handling(sample_raw_dataframe):
    """Verifies that +inf, -inf, and NaNs are safely sanitized and imputed."""
    cleaner = DataCleaner()
    cleaner.fit(sample_raw_dataframe)
    X, _, _ = cleaner.transform(sample_raw_dataframe)

    # Verify no infinities or NaNs remain in clean X dataframe
    assert not np.isinf(X.select_dtypes(include=[np.number])).values.any()
    assert not X.isnull().values.any()


# 5. Independent Processing (No Data Leakage between Train and Test)
def test_independent_processing_integrity():
    """
    Ensures scaler and imputer are fitted strictly on train and not refitted on test.
    """
    train_data = pd.DataFrame({
        "id": [1, 2],
        "dur": [10.0, 20.0],
        "proto": ["tcp", "udp"],
        "service": ["http", "dns"],
        "state": ["FIN", "CON"],
        "attack_cat": ["Normal", "DoS"],
        "label": [0, 1],
    })
    test_data = pd.DataFrame({
        "id": [3],
        "dur": [1000.0],  # Massive outlier
        "proto": ["tcp"],
        "service": ["http"],
        "state": ["FIN"],
        "attack_cat": ["Exploits"],
        "label": [1],
    })

    cleaner = DataCleaner()
    cleaner.fit(train_data)
    # The training median for dur should be 15.0
    assert cleaner.numeric_medians["dur"] == 15.0

    encoder = FeatureEncoder(numeric_cols=["dur"], categorical_cols=["proto", "service", "state"])
    X_train_clean, _, _ = cleaner.transform(train_data)
    X_test_clean, _, _ = cleaner.transform(test_data)

    encoder.fit(X_train_clean)
    train_mean = encoder.transformer.named_transformers_["num_scaler"].mean_[0]
    # Mean of [10.0, 20.0] is 15.0
    assert train_mean == 15.0

    # Transforming test_data must NOT alter the encoder's fitted mean
    _ = encoder.transform(X_test_clean)
    assert encoder.transformer.named_transformers_["num_scaler"].mean_[0] == 15.0


# 6. Encoder Resilience to Unseen Categories
def test_feature_encoder_handles_unseen_categories():
    """Tests that OneHotEncoder with handle_unknown='ignore' handles new categories gracefully."""
    train_df = pd.DataFrame({
        "proto": ["tcp", "udp"],
        "service": ["http", "dns"],
        "state": ["FIN", "CON"],
        "sbytes": [100.0, 200.0],
    })
    test_df = pd.DataFrame({
        "proto": ["icmp", "tcp"],  # 'icmp' unseen in train
        "service": ["ftp", "http"],  # 'ftp' unseen in train
        "state": ["INT", "FIN"],     # 'INT' unseen in train
        "sbytes": [150.0, 300.0],
    })

    encoder = FeatureEncoder(numeric_cols=["sbytes"], categorical_cols=["proto", "service", "state"])
    X_train_arr = encoder.fit_transform(train_df)
    X_test_arr = encoder.transform(test_df)

    assert X_train_arr.shape[1] == X_test_arr.shape[1], "Transformed dimensions must match exactly"
    assert not np.isnan(X_test_arr).any()
    assert not np.isinf(X_test_arr).any()


# 7. Processed Disk Artifacts Verification
def test_processed_disk_arrays_integrity():
    """Verifies exported .npy and .json artifacts exist, are finite, and match shapes."""
    summary_file = PROCESSED_DIR / "dataset_summary.json"
    pipeline_file = PROCESSED_DIR / "preprocessing_pipeline.joblib"
    feature_names_file = PROCESSED_DIR / "feature_names.json"

    # If processed files don't exist yet, we can skip or run pipeline
    if not summary_file.exists():
        pytest.skip("Processed artifacts not yet generated. Run pipeline.py first.")

    assert pipeline_file.exists()
    assert feature_names_file.exists()

    X_train = np.load(PROCESSED_DIR / "X_train.npy")
    X_val = np.load(PROCESSED_DIR / "X_val.npy")
    X_test = np.load(PROCESSED_DIR / "X_test.npy")

    y_train = np.load(PROCESSED_DIR / "y_train.npy")
    y_val = np.load(PROCESSED_DIR / "y_val.npy")
    y_test = np.load(PROCESSED_DIR / "y_test.npy")

    # Dimensions consistency
    assert X_train.shape[1] == X_val.shape[1] == X_test.shape[1]
    assert len(X_train) == len(y_train)
    assert len(X_val) == len(y_val)
    assert len(X_test) == len(y_test)

    # Numerical sanity: zero NaNs, zero Infinities
    assert not np.isnan(X_train).any()
    assert not np.isnan(X_val).any()
    assert not np.isnan(X_test).any()
    assert np.isfinite(X_train).all()
    assert np.isfinite(X_val).all()
    assert np.isfinite(X_test).all()

    # Targets binary check
    assert set(np.unique(y_train)).issubset({0, 1})
    assert set(np.unique(y_val)).issubset({0, 1})
    assert set(np.unique(y_test)).issubset({0, 1})


# 8. Pipeline Serialization & Inference Verification
def test_saved_pipeline_joblib_loading():
    """Verifies that preprocessing_pipeline.joblib can be loaded and used for inference."""
    pipeline_file = PROCESSED_DIR / "preprocessing_pipeline.joblib"
    if not pipeline_file.exists():
        pytest.skip("Pipeline joblib not yet created.")

    pipeline = PreprocessingPipeline.load_pipeline(pipeline_file)
    assert pipeline.is_fitted is True

    # Test dummy inference on a single sample from raw dataset
    raw_sample = pd.DataFrame([{
        "id": 999999,
        "dur": 0.001,
        "proto": "tcp",
        "service": "http",
        "state": "FIN",
        "spkts": 2,
        "dpkts": 2,
        "sbytes": 100,
        "dbytes": 200,
        "rate": 1000.0,
        "sttl": 64,
        "dttl": 128,
        "sload": 400000.0,
        "dload": 800000.0,
        "sloss": 0,
        "dloss": 0,
        "sinpkt": 0.001,
        "dinpkt": 0.001,
        "sjit": 0.0,
        "djit": 0.0,
        "swin": 255,
        "stcpb": 1000,
        "dtcpb": 1000,
        "dwin": 255,
        "tcprtt": 0.001,
        "synack": 0.0005,
        "ackdat": 0.0005,
        "smean": 50,
        "dmean": 100,
        "trans_depth": 0,
        "response_body_len": 0,
        "ct_srv_src": 1,
        "ct_state_ttl": 0,
        "ct_dst_ltm": 1,
        "ct_src_dport_ltm": 1,
        "ct_dst_sport_ltm": 1,
        "ct_dst_src_ltm": 1,
        "is_ftp_login": 0,
        "ct_ftp_cmd": 0,
        "ct_flw_http_mthd": 0,
        "ct_src_ltm": 1,
        "ct_srv_dst": 1,
        "is_sm_ips_ports": 0,
        "attack_cat": "Normal",
        "label": 0,
    }])

    transformed_sample = pipeline.transform_inference(raw_sample)
    assert isinstance(transformed_sample, np.ndarray)
    assert transformed_sample.shape[0] == 1
    assert transformed_sample.shape[1] == pipeline.encoder.total_transformed_features
    assert not np.isnan(transformed_sample).any()
    assert np.isfinite(transformed_sample).all()
