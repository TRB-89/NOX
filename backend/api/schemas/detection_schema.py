"""
NØX - Pydantic Request & Response Schemas
Type-safe data contracts for single-flow detection, batch detection,
CSV telemetry summaries, health status, and threat history.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class FlowRecordSchema(BaseModel):
    """
    Schema for a raw UNSW-NB15 network traffic flow record.
    Provides permissive types with default fallbacks for missing flow parameters.
    """
    model_config = ConfigDict(extra="allow")

    dur: Optional[float] = Field(0.0, description="Record duration in seconds")
    proto: Optional[str] = Field("tcp", description="Transaction protocol (e.g., tcp, udp, arp)")
    service: Optional[str] = Field("-", description="Application service (e.g., http, ftp, dns, -)")
    state: Optional[str] = Field("FIN", description="Flow state (e.g., FIN, INT, CON)")
    spkts: Optional[int] = Field(0, description="Source-to-destination packet count")
    dpkts: Optional[int] = Field(0, description="Destination-to-source packet count")
    sbytes: Optional[int] = Field(0, description="Source-to-destination byte count")
    dbytes: Optional[int] = Field(0, description="Destination-to-source byte count")
    rate: Optional[float] = Field(0.0, description="Packets per second rate")
    sttl: Optional[int] = Field(64, description="Source time-to-live")
    dttl: Optional[int] = Field(0, description="Destination time-to-live")
    sload: Optional[float] = Field(0.0, description="Source bits per second")
    dload: Optional[float] = Field(0.0, description="Destination bits per second")


class DetectionResponseSchema(BaseModel):
    """Prediction outcome for a single network flow record."""
    prediction: str = Field(..., description="'Normal Traffic' or 'Potential Attack'")
    class_id: int = Field(..., description="0 for Normal, 1 for Attack")
    attack_score: float = Field(..., description="Sigmoid confidence score in [0.0, 1.0]")
    threshold: float = Field(..., description="Classification threshold applied")
    severity: str = Field(..., description="'Normal', 'Low', 'Medium', or 'High'")
    model: str = Field(..., description="Model version tag")
    timestamp: str = Field(..., description="Timezone-aware ISO-8601 UTC timestamp")


class BatchDetectionRequest(BaseModel):
    """Batch prediction request containing multiple flow records."""
    records: List[FlowRecordSchema] = Field(..., description="List of raw flow records (max 5,000)")


class HealthResponseSchema(BaseModel):
    """Readiness and model status indicator."""
    status: str = Field(..., description="'ready' or 'uninitialized'")
    model_loaded: bool = Field(..., description="True if PyTorch model & pipeline are loaded")
    model_version: str = Field(..., description="Loaded neural model version tag")
    threshold: Optional[float] = Field(None, description="Active decision threshold")
    device: Optional[str] = Field(None, description="Computation device (cpu / cuda)")


class TelemetryStatsSchema(BaseModel):
    """Aggregate dashboard metrics computed from SQLite detection logs."""
    total_records_analyzed: int
    predicted_normal_count: int
    predicted_malicious_count: int
    attack_percentage: float
    severity_distribution: Dict[str, int]
    most_recent_detection_timestamp: Optional[str] = None


class CSVUploadResponseSchema(BaseModel):
    """Summary metrics returned after analyzing an uploaded CSV dataset."""
    status: str
    total_records_analyzed: int
    normal_traffic_count: int
    potential_attack_count: int
    attack_percentage: float
    severity_distribution: Dict[str, int]
    preview_limit: int
    preview_predictions: List[DetectionResponseSchema]
