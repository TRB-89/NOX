"""
NØX - Detection Service
Orchestrates raw flow preprocessing, neural inference, threat severity classification,
and automatic event persistence to the SQLite database.
"""

import datetime
import io
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from backend.services.model_service import ModelService
from backend.services.threat_service import ThreatService
from backend.database.models import DetectionEventDAO

logger = logging.getLogger("NOX.DetectionService")

MAX_BATCH_SIZE = 5000
MAX_UPLOAD_RECORDS = 50000


class DetectionService:
    """
    Central business logic coordinator for real-time and batch intrusion classification.
    """

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        event_dao: Optional[DetectionEventDAO] = None,
    ):
        self.model_service = model_service if model_service else ModelService()
        self.event_dao = event_dao if event_dao else DetectionEventDAO()

    def detect_single(
        self,
        flow_data: Dict[str, Any],
        source_type: str = "single",
    ) -> Dict[str, Any]:
        """
        Classifies a single raw network traffic flow record.
        Saves the event to SQLite and returns the enriched prediction payload.
        """
        # Convert dictionary to 1-row DataFrame
        df_raw = pd.DataFrame([flow_data])

        scores, preds = self.model_service.predict_from_raw(df_raw)
        score = float(scores[0])
        class_id = int(preds[0])
        threshold = self.model_service.threshold
        model_version = self.model_service.metadata.get("model_name", "NØX-MLP-v1")
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        is_attack = class_id == 1
        prediction_label = "Potential Attack" if is_attack else "Normal Traffic"
        severity = ThreatService.classify_severity(score=score, threshold=threshold)

        # Log event into SQLite
        try:
            self.event_dao.insert_event(
                timestamp=timestamp,
                prediction=prediction_label,
                class_id=class_id,
                attack_score=round(score, 4),
                threshold=threshold,
                severity=severity,
                model_version=model_version,
                source_type=source_type,
            )
        except Exception as e:
            logger.warning("Failed to persist detection event to SQLite: %s", e)

        return {
            "prediction": prediction_label,
            "class_id": class_id,
            "attack_score": round(score, 4),
            "threshold": threshold,
            "severity": severity,
            "model": model_version,
            "timestamp": timestamp,
        }

    def detect_batch(
        self,
        records: List[Dict[str, Any]],
        source_type: str = "batch",
    ) -> List[Dict[str, Any]]:
        """
        Classifies a list of raw network flow records in order.
        Persists events to SQLite and returns structured prediction list.
        """
        if not records:
            return []

        if len(records) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(records)} exceeds maximum allowable limit of {MAX_BATCH_SIZE} records.")

        df_raw = pd.DataFrame(records)
        scores, preds = self.model_service.predict_from_raw(df_raw)
        threshold = self.model_service.threshold
        model_version = self.model_service.metadata.get("model_name", "NØX-MLP-v1")
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        results = []
        events_to_log = []

        for score_val, class_id_val in zip(scores, preds):
            s = float(score_val)
            c = int(class_id_val)
            is_attack = c == 1
            pred_label = "Potential Attack" if is_attack else "Normal Traffic"
            severity = ThreatService.classify_severity(score=s, threshold=threshold)

            record_res = {
                "prediction": pred_label,
                "class_id": c,
                "attack_score": round(s, 4),
                "threshold": threshold,
                "severity": severity,
                "model": model_version,
                "timestamp": timestamp,
            }
            results.append(record_res)
            events_to_log.append({
                "timestamp": timestamp,
                "prediction": pred_label,
                "class_id": c,
                "attack_score": round(s, 4),
                "threshold": threshold,
                "severity": severity,
                "model_version": model_version,
                "source_type": source_type,
            })

        # Batch insert to database
        try:
            self.event_dao.insert_events_batch(events_to_log)
        except Exception as e:
            logger.warning("Batch database insert failed: %s", e)

        return results

    def process_csv_upload(
        self,
        file_bytes: bytes,
        chunk_size: int = 5000,
        max_preview: int = 25,
    ) -> Dict[str, Any]:
        """
        Streams and classifies an uploaded CSV file in bounded memory chunks.
        Validates headers, strips ground truth labels, tallies predictions,
        and logs events into SQLite.
        """
        try:
            # Read first row to validate CSV headers
            preview_df = pd.read_csv(io.BytesIO(file_bytes), nrows=5, encoding="utf-8-sig")
        except Exception as e:
            raise ValueError(f"Malformed or unreadable CSV file: {e}")

        # Check for core flow features
        essential_test = ["proto", "state", "dur", "sbytes", "dbytes"]
        cols = list(preview_df.columns)
        missing = [c for c in essential_test if c not in cols]
        if missing:
            raise ValueError(f"CSV missing essential network flow columns: {missing}")

        # Stream process in bounded chunks to prevent high memory consumption
        csv_stream = io.StringIO(file_bytes.decode("utf-8-sig", errors="replace"))

        total_analyzed = 0
        normal_count = 0
        attack_count = 0
        severity_dist = {"Normal": 0, "Low": 0, "Medium": 0, "High": 0}
        preview_results = []
        events_to_log = []

        model_version = self.model_service.metadata.get("model_name", "NØX-MLP-v1")
        threshold = self.model_service.threshold

        for chunk_df in pd.read_csv(csv_stream, chunksize=chunk_size, low_memory=False):
            if total_analyzed + len(chunk_df) > MAX_UPLOAD_RECORDS:
                raise ValueError(
                    f"Uploaded dataset exceeds safety limit of {MAX_UPLOAD_RECORDS:,} records. "
                    "Please split file into smaller batches."
                )

            # Strip target labels if present to avoid any leakage or interference
            for col in ["label", "attack_cat", "id"]:
                if col in chunk_df.columns:
                    chunk_df = chunk_df.drop(columns=[col])

            scores, preds = self.model_service.predict_from_raw(chunk_df)
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

            for s, c in zip(scores, preds):
                score_val = float(s)
                class_id_val = int(c)
                pred_label = "Potential Attack" if class_id_val == 1 else "Normal Traffic"
                severity = ThreatService.classify_severity(score=score_val, threshold=threshold)

                if class_id_val == 1:
                    attack_count += 1
                else:
                    normal_count += 1
                severity_dist[severity] = severity_dist.get(severity, 0) + 1

                res_dict = {
                    "prediction": pred_label,
                    "class_id": class_id_val,
                    "attack_score": round(score_val, 4),
                    "threshold": threshold,
                    "severity": severity,
                    "model": model_version,
                    "timestamp": timestamp,
                }

                if len(preview_results) < max_preview:
                    preview_results.append(res_dict)

                events_to_log.append({
                    "timestamp": timestamp,
                    "prediction": pred_label,
                    "class_id": class_id_val,
                    "attack_score": round(score_val, 4),
                    "threshold": threshold,
                    "severity": severity,
                    "model_version": model_version,
                    "source_type": "csv_upload",
                })

            total_analyzed += len(chunk_df)

        # Batch insert to SQLite
        try:
            self.event_dao.insert_events_batch(events_to_log)
        except Exception as e:
            logger.warning("Failed to log CSV detection events to database: %s", e)

        return {
            "status": "success",
            "total_records_analyzed": total_analyzed,
            "normal_traffic_count": normal_count,
            "potential_attack_count": attack_count,
            "attack_percentage": round((attack_count / total_analyzed * 100), 2) if total_analyzed > 0 else 0.0,
            "severity_distribution": severity_dist,
            "preview_limit": max_preview,
            "preview_predictions": preview_results,
        }
