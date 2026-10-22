import {
  HealthStatus,
  TelemetryStats,
  DetectionResult,
  CSVUploadResponse,
  DetectionEvent,
  FlowRecord,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        let errorMessage = `Server error (${response.status})`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // Response was not JSON
        }
        throw new Error(errorMessage);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error('Backend unavailable. Start the NØX FastAPI server to enable detection.');
      }
      throw err;
    }
  }

  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/api/health');
  }

  async getStats(): Promise<TelemetryStats> {
    return this.request<TelemetryStats>('/api/stats');
  }

  async getHistory(limit: number = 50, offset: number = 0, sourceType?: string): Promise<DetectionEvent[]> {
    let query = `/api/history?limit=${limit}&offset=${offset}`;
    if (sourceType) {
      query += `&source_type=${encodeURIComponent(sourceType)}`;
    }
    return this.request<DetectionEvent[]>(query);
  }

  async detectSingle(record: FlowRecord): Promise<DetectionResult> {
    return this.request<DetectionResult>('/api/detect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(record),
    });
  }

  async detectBatch(records: FlowRecord[]): Promise<DetectionResult[]> {
    return this.request<DetectionResult[]>('/api/detect/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ records }),
    });
  }

  async uploadCSV(file: File): Promise<CSVUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<CSVUploadResponse>('/api/detect/upload', {
      method: 'POST',
      body: formData,
    });
  }
}

export const api = new ApiService(API_BASE_URL);
