"""
NØX - Neural Network Intrusion Detection System
Module 02: Offline Dataset Demonstration Script

Demonstrates offline dataset inference using the trained PyTorch Multilayer Perceptron.
Loads a representative sample of preprocessed UNSW-NB15 test flow vectors, generates
model classifications, compares predictions against ground truth, and outputs telemetry.

NOTE: This is an offline benchmark demonstration on historical recorded network traces.
It does not perform live network packet capture or real-time inline monitoring.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
from backend.inference.predict import NoxPredictor


def run_demo(sample_count: int = 15):
    """Runs interactive CLI demonstration on test set records."""
    print("\n" + "=" * 78)
    print(" NØX INTRUSION DETECTION SYSTEM — OFFLINE DATASET INFERENCE DEMONSTRATION")
    print(" (Historical Benchmark: UNSW-NB15 Test Partition)")
    print("=" * 78)

    base_dir = Path(__file__).resolve().parent
    processed_dir = base_dir / "data" / "processed"

    x_test_path = processed_dir / "X_test.npy"
    y_test_path = processed_dir / "y_test.npy"
    attack_cat_path = processed_dir / "attack_cat_test.npy"

    if not x_test_path.exists() or not y_test_path.exists():
        print(f"[!] Error: Test arrays not found in {processed_dir}")
        print("    Please run preprocessing first: python backend/preprocessing/pipeline.py")
        return

    # Load test slice
    X_test = np.load(x_test_path)
    y_test = np.load(y_test_path)
    attack_cats = np.load(attack_cat_path) if attack_cat_path.exists() else None

    # Pick a balanced slice of both Normal and various Attack records
    normal_indices = np.where(y_test == 0)[0][:sample_count // 2]
    attack_indices = np.where(y_test == 1)[0][:sample_count - len(normal_indices)]
    selected_indices = np.concatenate([normal_indices, attack_indices])
    np.random.seed(42)
    np.random.shuffle(selected_indices)

    # Initialize Predictor
    predictor = NoxPredictor()

    print(f"\n[+] Loaded {len(selected_indices)} sample network flow records for offline inference.")
    print(f"[+] Model: {predictor.model_name} | Decision Threshold: {predictor.threshold:.2f}")
    print("-" * 78)
    print(f"{'Idx':<6}{'Category':<16}{'True Label':<14}{'Prediction':<18}{'Score':<10}{'Match?':<8}")
    print("-" * 78)

    correct_count = 0
    total_count = len(selected_indices)

    for i, idx in enumerate(selected_indices, start=1):
        x_sample = X_test[idx]
        y_true = int(y_test[idx])
        true_name = "Normal (0)" if y_true == 0 else "Attack (1)"
        cat_name = str(attack_cats[idx]) if attack_cats is not None else "N/A"

        pred_res = predictor.predict_single(x_sample)
        pred_label = pred_res["prediction"]
        pred_class = pred_res["class_id"]
        score = pred_res["attack_score"]

        is_match = (y_true == pred_class)
        if is_match:
            correct_count += 1
            match_str = "[OK]"
        else:
            match_str = "[MISMATCH]"

        print(f"#{i:<5}{cat_name:<16}{true_name:<14}{pred_label:<18}{score:<10.4f}{match_str:<8}")

    print("-" * 78)
    accuracy_pct = (correct_count / total_count) * 100
    print(f"Demonstration Summary:")
    print(f"  Total Processed:         {total_count} flows")
    print(f"  Correct Classifications: {correct_count} flows")
    print(f"  Sample Accuracy:         {accuracy_pct:.2f}%")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    run_demo()
