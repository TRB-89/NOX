"""
NØX - Threat Severity Classification Service
Maps binary neural classification scores and decision thresholds into
triaged threat severity levels (Normal, Low, Medium, High).
"""

from typing import Dict, Any


class ThreatService:
    """
    Categorizes detection scores into operational threat priority tiers:
    - Normal: Below classification threshold (or class_id == 0).
    - Low: Threshold <= score < min(threshold + 0.20, 0.75).
    - Medium: Above Low tier, below 0.90.
    - High: Score >= 0.90.

    NOTE: Severity levels are rule-based UI prioritization indicators for SOC operators,
    not validated measurements of real-world vulnerability impact or CVSS ratings.
    """

    @staticmethod
    def classify_severity(score: float, threshold: float = 0.50) -> str:
        """
        Calculates threat severity based on the attack confidence score and threshold.
        """
        # If below threshold, traffic is benign
        if score < threshold:
            return "Normal"

        # Determine dynamic boundaries consistent with threshold
        low_bound = threshold
        high_bound = 0.90
        med_bound = max(low_bound + (high_bound - low_bound) * 0.5, 0.70)

        if score < med_bound:
            return "Low"
        elif score < high_bound:
            return "Medium"
        else:
            return "High"

    @classmethod
    def enrich_detection(cls, prediction_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a raw prediction dictionary with the computed severity tier.
        """
        score = float(prediction_dict.get("attack_score", 0.0))
        threshold = float(prediction_dict.get("threshold", 0.50))
        severity = cls.classify_severity(score=score, threshold=threshold)
        prediction_dict["severity"] = severity
        return prediction_dict
