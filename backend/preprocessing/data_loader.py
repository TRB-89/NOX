"""
NØX - Neural Network Intrusion Detection System
Module 01: Data Loader

Responsible for detecting, loading, schema-validating, and inspecting the official
UNSW-NB15 network traffic datasets (UNSW_NB15_training-set.csv and UNSW_NB15_testing-set.csv).
"""

from pathlib import Path
import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NOX.DataLoader")

TRAIN_FILENAME = "UNSW_NB15_training-set.csv"
TEST_FILENAME = "UNSW_NB15_testing-set.csv"

# Key expected columns in official UNSW-NB15 benchmark files
ESSENTIAL_COLUMNS = [
    "id",
    "dur",
    "proto",
    "service",
    "state",
    "spkts",
    "dpkts",
    "sbytes",
    "dbytes",
    "rate",
    "sttl",
    "dttl",
    "sload",
    "dload",
    "attack_cat",
    "label",
]


class DataLoader:
    """
    Handles file detection, ingestion, schema validation, and statistical inspection
    for the UNSW-NB15 intrusion detection dataset.
    """

    def __init__(self, raw_data_dir: Optional[Path | str] = None):
        if raw_data_dir is None:
            self.raw_data_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
        else:
            self.raw_data_dir = Path(raw_data_dir)

        self.train_path = self.raw_data_dir / TRAIN_FILENAME
        self.test_path = self.raw_data_dir / TEST_FILENAME

    def check_files_exist(self) -> Dict[str, bool]:
        """
        Check whether the required UNSW-NB15 CSV files exist and have valid size.
        """
        return {
            TRAIN_FILENAME: self.train_path.is_file() and self.train_path.stat().st_size > 1000,
            TEST_FILENAME: self.test_path.is_file() and self.test_path.stat().st_size > 1000,
        }

    def get_download_instructions(self) -> str:
        """
        Returns clear instructions for downloading and placing the official dataset files.
        """
        instructions = (
            "\n" + "=" * 76 + "\n"
            " [!] MISSING DATASET NOTIFICATION — NØX PREPROCESSING PIPELINE\n"
            "=" * 76 + "\n"
            "The required official UNSW-NB15 benchmark files were not found in:\n"
            f"  {self.raw_data_dir.resolve()}\n\n"
            "Required Files:\n"
            f"  1. {TRAIN_FILENAME}\n"
            f"  2. {TEST_FILENAME}\n\n"
            "HOW TO OBTAIN THE DATASET:\n"
            "  Option A (Automatic Utility):\n"
            "    Run the built-in downloader:\n"
            "    PowerShell: .venv\\Scripts\\python backend/utils/download_dataset.py\n\n"
            "  Option B (Manual Portal Download):\n"
            "    1. Open official UNSW-NB15 repository:\n"
            "       https://research.unsw.edu.au/projects/unsw-nb15-dataset\n"
            "       or Kaggle mirror: https://www.kaggle.com/datasets/mrwellsdavid/unsw-nb15\n"
            f"    2. Download '{TRAIN_FILENAME}' and '{TEST_FILENAME}'.\n"
            f"    3. Copy both files into: '{self.raw_data_dir.resolve()}'\n"
            "=" * 76
        )
        return instructions

    def load_raw_datasets(
        self,
        encoding: str = "utf-8",
        raise_on_missing: bool = True,
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Loads training and testing CSV files into pandas DataFrames.
        Handles errors gracefully and displays download instructions if files are absent.
        """
        file_status = self.check_files_exist()
        missing = [f for f, exists in file_status.items() if not exists]

        if missing:
            msg = self.get_download_instructions()
            print(msg)
            if raise_on_missing:
                raise FileNotFoundError(
                    f"Required raw dataset files missing in '{self.raw_data_dir}': {missing}"
                )
            return None, None

        try:
            logger.info("Loading training dataset from %s ...", self.train_path)
            # Try utf-8-sig first to properly strip BOM if present
            train_df = pd.read_csv(self.train_path, encoding="utf-8-sig", low_memory=False)
            logger.info("Training dataset loaded successfully. Shape: %s", train_df.shape)

            logger.info("Loading testing dataset from %s ...", self.test_path)
            test_df = pd.read_csv(self.test_path, encoding="utf-8-sig", low_memory=False)
            logger.info("Testing dataset loaded successfully. Shape: %s", test_df.shape)

            # Strip any accidental whitespace in column names
            train_df.columns = [c.strip() for c in train_df.columns]
            test_df.columns = [c.strip() for c in test_df.columns]

            return train_df, test_df

        except Exception as e:
            logger.error("Failed to load raw datasets: %s", str(e), exc_info=True)
            if raise_on_missing:
                raise
            return None, None

    def validate_schema(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """
        Validates column names, target presence, and data types against expected UNSW-NB15 schema.
        """
        cols = list(df.columns)
        missing_essential = [col for col in ESSENTIAL_COLUMNS if col not in cols]

        has_target = "label" in cols
        has_attack_cat = "attack_cat" in cols

        # Check binary target values
        valid_binary_target = False
        if has_target:
            unique_labels = set(df["label"].dropna().unique())
            valid_binary_target = unique_labels.issubset({0, 1})

        validation_result = {
            "dataset_name": dataset_name,
            "total_columns": len(cols),
            "columns": cols,
            "missing_essential_columns": missing_essential,
            "is_schema_valid": len(missing_essential) == 0,
            "has_binary_label": has_target,
            "valid_binary_target": valid_binary_target,
            "has_attack_category": has_attack_cat,
        }

        if missing_essential:
            logger.warning(
                "[%s] Missing essential columns: %s", dataset_name, missing_essential
            )
        else:
            logger.info("[%s] Schema validation PASSED. All core columns present.", dataset_name)

        return validation_result

    def inspect_dataset(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """
        Calculates and displays comprehensive statistical profile:
        - Record count and feature count
        - Missing value statistics
        - Normal vs Malicious traffic distribution
        - Attack categories breakdown
        - Data types breakdown
        """
        total_records, total_features = df.shape

        # Missing values
        missing_series = df.isnull().sum()
        total_missing_cells = int(missing_series.sum())
        cols_with_missing = missing_series[missing_series > 0].to_dict()

        # Target label distribution
        label_dist = {}
        if "label" in df.columns:
            counts = df["label"].value_counts(dropna=False).to_dict()
            total = len(df["label"])
            label_dist = {
                int(k) if pd.notnull(k) else "NaN": {
                    "count": int(v),
                    "percentage": round((v / total) * 100, 2),
                    "class_name": "Normal Traffic" if k == 0 else ("Malicious Traffic" if k == 1 else "Unknown"),
                }
                for k, v in counts.items()
            }

        # Attack categories distribution
        attack_cat_dist = {}
        if "attack_cat" in df.columns:
            # Standardize empty/whitespace entries
            clean_cats = df["attack_cat"].fillna("Normal").astype(str).str.strip()
            cat_counts = clean_cats.value_counts().to_dict()
            total = len(clean_cats)
            attack_cat_dist = {
                str(cat): {
                    "count": int(cnt),
                    "percentage": round((cnt / total) * 100, 2),
                }
                for cat, cnt in cat_counts.items()
            }

        # Data types count
        dtypes_counts = {str(k): int(v) for k, v in df.dtypes.value_counts().to_dict().items()}

        summary = {
            "dataset_name": dataset_name,
            "total_records": total_records,
            "total_features": total_features,
            "total_missing_cells": total_missing_cells,
            "columns_with_missing": cols_with_missing,
            "label_distribution": label_dist,
            "attack_category_distribution": attack_cat_dist,
            "dtypes_breakdown": dtypes_counts,
        }

        # Print human-readable inspection report
        self._print_inspection_report(summary)
        return summary

    def _print_inspection_report(self, summary: Dict[str, Any]) -> None:
        """Pretty-prints inspection metrics to stdout."""
        name = summary["dataset_name"]
        print("\n" + "=" * 65)
        print(f" NØX DATA INSPECTION REPORT — [{name.upper()}]")
        print("=" * 65)
        print(f"Total Traffic Records:   {summary['total_records']:,}")
        print(f"Total Features (Columns): {summary['total_features']}")
        print(f"Missing Values:          {summary['total_missing_cells']} cells")
        if summary["columns_with_missing"]:
            print("  Columns with Missing Values:")
            for col, count in summary["columns_with_missing"].items():
                print(f"    - {col}: {count:,}")
        else:
            print("  (No missing values detected in raw frame)")

        print("-" * 65)
        print("Binary Traffic Distribution (label):")
        for lbl, stats in summary["label_distribution"].items():
            name_str = stats.get("class_name", str(lbl))
            print(f"  [{lbl}] {name_str:<18}: {stats['count']:>8,} ({stats['percentage']:>5.2f}%)")

        print("-" * 65)
        print("Attack Categories Distribution (attack_cat):")
        for cat, stats in summary["attack_category_distribution"].items():
            print(f"  {cat:<22}: {stats['count']:>8,} ({stats['percentage']:>5.2f}%)")
        print("=" * 65 + "\n")
