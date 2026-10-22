/**
 * Type definitions matching NØX FastAPI backend schemas.
 */

export interface HealthStatus {
  status: 'ready' | 'uninitialized' | 'error';
  model_loaded: boolean;
  model_version: string;
  threshold: number | null;
  device: string | null;
}

export interface TelemetryStats {
  total_records_analyzed: number;
  predicted_normal_count: number;
  predicted_malicious_count: number;
  attack_percentage: number;
  severity_distribution: {
    Normal: number;
    Low: number;
    Medium: number;
    High: number;
  };
  most_recent_detection_timestamp: string | null;
}

export interface DetectionResult {
  prediction: string;
  class_id: number;
  attack_score: number;
  threshold: number;
  severity: 'Normal' | 'Low' | 'Medium' | 'High';
  model: string;
  timestamp: string;
}

export interface CSVUploadResponse {
  status: string;
  total_records_analyzed: number;
  normal_traffic_count: number;
  potential_attack_count: number;
  attack_percentage: number;
  severity_distribution: {
    Normal: number;
    Low: number;
    Medium: number;
    High: number;
  };
  preview_limit: number;
  preview_predictions: DetectionResult[];
}

export interface DetectionEvent {
  id: number;
  timestamp: string;
  prediction: string;
  class_id: number;
  attack_score: number;
  threshold: number;
  severity: 'Normal' | 'Low' | 'Medium' | 'High';
  model_version: string;
  source_type: string;
}

export interface FlowRecord {
  dur?: number;
  proto?: string;
  service?: string;
  state?: string;
  spkts?: number;
  dpkts?: number;
  sbytes?: number;
  dbytes?: number;
  rate?: number;
  sttl?: number;
  dttl?: number;
  sload?: number;
  dload?: number;
  [key: string]: any;
}

export interface ModelEvaluationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  roc_auc: number;
  confusion_matrix: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
  };
  threshold_used: number;
}
