import {
  HealthStatus,
  TelemetryStats,
  DetectionResult,
  CSVUploadResponse,
  DetectionEvent,
  FlowRecord,
} from '../types';

/**
 * Resolves the appropriate backend API Base URL based on environment.
 * Prevents using localhost in cloud/production environments.
 */
export function resolveApiBaseUrl(): string {
  // 1. Check runtime localStorage override (allows dynamic re-targeting if desired)
  if (typeof window !== 'undefined') {
    try {
      const override = localStorage.getItem('nox_api_base_url');
      if (override && override.trim()) {
        return sanitizeUrl(override.trim());
      }
    } catch {
      // LocalStorage access restricted in some iframes
    }
  }

  // 2. Read Vite environment variable
  const envUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  const isDev = import.meta.env.DEV;
  const isLocalClient =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  const isCloudHost = typeof window !== 'undefined' && !isLocalClient;

  if (envUrl) {
    const cleaned = sanitizeUrl(envUrl);
    const isEnvLocal = cleaned.includes('localhost') || cleaned.includes('127.0.0.1');

    // Security guard: If deploying to production (e.g. Vercel), do NOT use localhost!
    if ((isCloudHost || !isDev) && isEnvLocal) {
      console.warn(
        `[NØX Configuration Notice] VITE_API_BASE_URL points to "${cleaned}", which is unreachable in a production cloud environment. Falling back to live Render backend: https://nox-neural-backend.onrender.com`
      );
      return 'https://nox-neural-backend.onrender.com';
    }
    return cleaned;
  }

  // 3. Fallbacks when VITE_API_BASE_URL is not set:
  // If running on a cloud hostname (e.g. *.vercel.app), NEVER default to localhost!
  if (isCloudHost) {
    return 'https://nox-neural-backend.onrender.com';
  }

  if (isDev || isLocalClient) {
    return 'http://127.0.0.1:8000';
  }

  // Production fallback — never use localhost in production
  return 'https://nox-neural-backend.onrender.com';
}

function sanitizeUrl(url: string): string {
  let cleaned = url.replace(/['"]+/g, '').trim().replace(/\/+$/, '');
  // Auto-upgrade http:// to https:// when loaded over HTTPS to prevent Mixed Content security blocks
  if (
    typeof window !== 'undefined' &&
    window.location.protocol === 'https:' &&
    cleaned.startsWith('http://') &&
    !cleaned.includes('localhost') &&
    !cleaned.includes('127.0.0.1')
  ) {
    cleaned = cleaned.replace(/^http:\/\//, 'https://');
  }
  return cleaned;
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export class ApiService {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ? sanitizeUrl(baseUrl) : resolveApiBaseUrl();
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setBaseUrl(url: string): void {
    this.baseUrl = sanitizeUrl(url);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('nox_api_base_url', this.baseUrl);
      } catch {
        // Ignored
      }
    }
  }

  resetBaseUrl(): void {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('nox_api_base_url');
      } catch {
        // Ignored
      }
    }
    this.baseUrl = resolveApiBaseUrl();
  }

  isLocalhost(): boolean {
    return this.baseUrl.includes('127.0.0.1') || this.baseUrl.includes('localhost');
  }

  private async request<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const timeoutMs = options?.timeoutMs ?? (endpoint.includes('/upload') ? 60000 : 20000);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const fetchOptions: RequestInit = {
        ...options,
        signal: options?.signal || controller.signal,
      };

      const response = await fetch(url, fetchOptions);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = `Server responded with HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // Response body was not JSON
        }
        throw new Error(errorMessage);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      clearTimeout(timeoutId);
      throw this.categorizeError(err, url, timeoutMs);
    }
  }

  private categorizeError(err: any, url: string, timeoutMs: number): Error {
    // 1. Timeout / Abort
    if (err.name === 'AbortError') {
      return new Error(
        `Connection timed out (${timeoutMs / 1000}s) waiting for ${url}. If using Render Free Tier, the backend container may be spinning up from sleep (~60-90s). Please wait and retry.`
      );
    }

    // 2. Client is completely offline
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      return new Error('Your browser is offline. Please check your internet connectivity.');
    }

    // 3. Mixed Content block
    const isClientHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
    if (isClientHttps && url.startsWith('http://') && !url.includes('localhost')) {
      return new Error(
        `Mixed Content Blocked: HTTPS frontend cannot query insecure HTTP backend at "${url}". Configure VITE_API_BASE_URL to an HTTPS endpoint.`
      );
    }

    // 4. Production app pointing to localhost
    if (
      typeof window !== 'undefined' &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1' &&
      (url.includes('localhost') || url.includes('127.0.0.1'))
    ) {
      return new Error(
        `Localhost Inaccessible: Cloud deployment cannot communicate with client localhost (${url}). Ensure VITE_API_BASE_URL points to your live Render backend in Vercel settings.`
      );
    }

    // 5. Network / CORS failure
    const msg = (err.message || '').toLowerCase();
    if (
      err.name === 'TypeError' ||
      msg.includes('failed to fetch') ||
      msg.includes('network') ||
      msg.includes('load failed')
    ) {
      return new Error(
        `NØX backend at ${url} is unreachable. The service may be cold-starting on Render (~60–90s) or CORS origin policy may need verification.`
      );
    }

    return err instanceof Error ? err : new Error(String(err));
  }

  /**
   * Health and model readiness query.
   * Probes /api/health with automatic fallback to /health.
   */
  async getHealth(timeoutMs: number = 12000): Promise<HealthStatus> {
    try {
      return await this.request<HealthStatus>('/api/health', { timeoutMs });
    } catch (primaryErr) {
      try {
        return await this.request<HealthStatus>('/health', { timeoutMs });
      } catch {
        throw primaryErr;
      }
    }
  }

  async getStats(timeoutMs: number = 20000): Promise<TelemetryStats> {
    return this.request<TelemetryStats>('/api/stats', { timeoutMs });
  }

  async getHistory(
    limit: number = 50,
    offset: number = 0,
    sourceType?: string,
    timeoutMs: number = 20000
  ): Promise<DetectionEvent[]> {
    let query = `/api/history?limit=${limit}&offset=${offset}`;
    if (sourceType) {
      query += `&source_type=${encodeURIComponent(sourceType)}`;
    }
    return this.request<DetectionEvent[]>(query, { timeoutMs });
  }

  async detectSingle(record: FlowRecord, timeoutMs: number = 25000): Promise<DetectionResult> {
    return this.request<DetectionResult>('/api/detect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(record),
      timeoutMs,
    });
  }

  async detectBatch(records: FlowRecord[], timeoutMs: number = 35000): Promise<DetectionResult[]> {
    return this.request<DetectionResult[]>('/api/detect/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ records }),
      timeoutMs,
    });
  }

  async uploadCSV(file: File, timeoutMs: number = 60000): Promise<CSVUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<CSVUploadResponse>('/api/detect/upload', {
      method: 'POST',
      body: formData,
      timeoutMs,
    });
  }
}

export const api = new ApiService();
