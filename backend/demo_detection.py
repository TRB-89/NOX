"""
NØX - Neural Network Intrusion Detection System
Module 03: Offline Detection Demonstration Script

Demonstrates the integrated intrusion detection engine, threat severity classification,
and SQLite database event persistence using real flow samples from the UNSW-NB15 test set.

NOTE: This is an offline benchmark demonstration. It evaluates historical recorded network flows
and does NOT perform live network packet capture or live firewall modifications.
"""

import sys
from pathlib import Path

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pandas as pd
from backend.database.db import init_db
from backend.database.models import DetectionEventDAO
from backend.services.model_service import ModelService
from backend.services.detection_service import DetectionService


def run_demo(sample_count: int = 12):
    print("\n" + "=" * 80)
    print(" NØX INTRUSION DETECTION ENGINE — OFFLINE END-TO-END DEMONSTRATION")
    print(" (Neural Inference + Threat Severity Triage + SQLite Event Logging)")
    print("=" * 80)

    # 1. Initialize SQLite database & Model Service
    print("[*] Initializing SQLite database schema...")
    init_db()

    print("[*] Loading PyTorch model and preprocessing pipeline...")
    model_service = ModelService()
    model_service.load_artifacts()

    event_dao = DetectionEventDAO()
    detection_service = DetectionService(model_service=model_service, event_dao=event_dao)

    # 2. Load raw test samples from raw CSV
    raw_test_csv = _project_root / "backend" / "data" / "raw" / "UNSW_NB15_testing-set.csv"
    if not raw_test_csv.exists():
        print(f"[!] Test CSV not found at {raw_test_csv}. Please run pipeline first.")
        return

    print(f"[*] Sampling {sample_count} flow records from {raw_test_csv.name}...")
    df_raw = pd.read_csv(raw_test_csv, encoding="utf-8-sig", nrows=2000)

    # Pick balanced sample of Normal and Attack flows
    normal_sample = df_raw[df_raw["label"] == 0].head(sample_count // 2)
    attack_sample = df_raw[df_raw["label"] == 1].head(sample_count - len(normal_sample))
    combined_sample = pd.concat([normal_sample, attack_sample]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    print("-" * 80)
    print(f"{'Idx':<5}{'Category':<16}{'True Label':<14}{'Prediction':<18}{'Score':<9}{'Severity':<10}{'Logged?'}")
    print("-" * 80)

    attacks_detected = 0
    correct_classifications = 0

    for idx, row in combined_sample.iterrows():
        # Separate ground truth label and category for display only
        ground_truth = int(row["label"])
        true_name = "Normal (0)" if ground_truth == 0 else "Attack (1)"
        category = str(row.get("attack_cat", "Normal"))

        # Strip target fields before passing to detection engine (strictly prevent leakage)
        flow_record = row.drop(labels=["label", "attack_cat", "id"], errors="ignore").to_dict()

        # Run detection engine
        result = detection_service.detect_single(flow_record, source_type="demo")

        pred_label = result["prediction"]
        class_id = result["class_id"]
        score = result["attack_score"]
        severity = result["severity"]

        if class_id == 1:
            attacks_detected += 1
        if class_id == ground_truth:
            correct_classifications += 1

        print(f"#{idx+1:<4}{category:<16}{true_name:<14}{pred_label:<18}{score:<9.4f}{severity:<10}[SQLite OK]")

    print("-" * 80)
    print("DETECTION ENGINE SUMMARY:")
    print(f"  Total Flows Evaluated:     {len(combined_sample)}")
    print(f"  Potential Attacks Detected: {attacks_detected}")
    print(f"  Classification Match Rate: {correct_classifications}/{len(combined_sample)} ({correct_classifications/len(combined_sample)*100:.1f}%)")

    # 3. Retrieve Live Telemetry Stats from Database
    print("\n[*] Querying live SQLite telemetry statistics (/api/stats)...")
    stats = event_dao.get_telemetry_stats()
    print(f"  Total Recorded in DB:      {stats['total_records_analyzed']} events")
    print(f"  Historical Attack Tally:   {stats['predicted_malicious_count']} attacks ({stats['attack_percentage']}%)")
    print(f"  Severity Distribution:     {stats['severity_distribution']}")
    print(f"  Most Recent Event Logged:  {stats['most_recent_detection_timestamp']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
