import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { HealthStatus } from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import {
  Server,
  Cpu,
  Database,
  Layers,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Terminal,
  Activity,
  Code2,
} from 'lucide-react';

export const System: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pingTimeMs, setPingTimeMs] = useState<number | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const data = await api.getHealth();
      const end = performance.now();
      setHealth(data);
      setPingTimeMs(Math.round(end - start));
    } catch (err: any) {
      setError(err.message || 'FastAPI system health query failed.');
      setHealth(null);
      setPingTimeMs(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-xs uppercase tracking-widest text-accent font-semibold">
              05 // SYSTEM DIAGNOSTICS
            </span>
            <span className="text-muted font-mono text-xs">•</span>
            <span className="font-mono text-xs text-muted">ENVIRONMENT & RUNTIME</span>
          </div>
          <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight text-chrome">
            SYSTEM INFORMATION
          </h1>
          <p className="font-sans text-sm text-muted mt-2 max-w-2xl">
            Live health verification, runtime environment telemetry, and neural network parameter diagnostics.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          disabled={isLoading}
          className="px-4 py-2 border border-border text-chrome hover:border-chrome text-xs font-mono uppercase tracking-wider flex items-center gap-2 self-start md:self-auto transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>QUERY ENDPOINT</span>
        </button>
      </div>

      {/* Dynamic Health Status Banner */}
      <div className="border-industrial bg-surface p-6">
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-3">
            {isLoading ? (
              <div className="w-3 h-3 rounded-full bg-muted animate-pulse" />
            ) : health?.status === 'ready' ? (
              <div className="w-3 h-3 rounded-full bg-success animate-pulse" />
            ) : (
              <div className="w-3 h-3 rounded-full bg-critical" />
            )}
            <div>
              <span className="font-mono text-[10px] uppercase text-muted tracking-widest block">
                API HEALTH TELEMETRY
              </span>
              <h3 className="font-display text-lg font-bold uppercase text-chrome">
                {isLoading
                  ? 'PROBING BACKEND...'
                  : health?.status === 'ready'
                  ? 'FASTAPI BACKEND OPERATIONAL'
                  : 'BACKEND OFFLINE / UNINITIALIZED'}
              </h3>
            </div>
          </div>

          {pingTimeMs !== null && (
            <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-muted border border-border px-3 py-1">
              <Activity className="w-3.5 h-3.5 text-success" />
              <span>LATENCY: {pingTimeMs} MS</span>
            </div>
          )}
        </div>

        {error ? (
          <div className="mt-4 p-4 border border-critical/50 bg-critical/10 text-critical font-mono text-xs flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 font-mono text-xs">
            <div className="p-3 bg-surface-elevated border border-border">
              <span className="text-[10px] text-muted uppercase block">MODEL LOADED</span>
              <span className={`text-sm font-bold ${health?.model_loaded ? 'text-success' : 'text-critical'}`}>
                {health?.model_loaded ? 'ONLINE (IN MEMORY)' : 'NOT LOADED'}
              </span>
            </div>

            <div className="p-3 bg-surface-elevated border border-border">
              <span className="text-[10px] text-muted uppercase block">MODEL VERSION</span>
              <span className="text-sm font-bold text-chrome">
                {health?.model_version || 'N/A'}
              </span>
            </div>

            <div className="p-3 bg-surface-elevated border border-border">
              <span className="text-[10px] text-muted uppercase block">DECISION THRESHOLD</span>
              <span className="text-sm font-bold text-chrome">
                {health?.threshold !== null ? health?.threshold : 'N/A'}
              </span>
            </div>

            <div className="p-3 bg-surface-elevated border border-border">
              <span className="text-[10px] text-muted uppercase block">COMPUTE DEVICE</span>
              <span className="text-sm font-bold text-chrome uppercase">
                {health?.device || 'N/A'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Static Technical Architecture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core System Components */}
        <div className="border-industrial bg-surface p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Server className="w-4 h-4 text-chrome" />
            <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
              APPLICATION & ARCHITECTURE
            </h3>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">APPLICATION</span>
              <span className="text-chrome font-semibold">NØX — Neural Network Intrusion Detection</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">MODEL TYPE</span>
              <span className="text-chrome font-semibold">PyTorch Multilayer Perceptron (MLP)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">DETECTION MODE</span>
              <span className="text-chrome font-semibold">Offline dataset-based flow classification</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">BENCHMARK DATASET</span>
              <span className="text-chrome font-semibold">UNSW-NB15 (Raw network flows)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">BACKEND RUNTIME</span>
              <span className="text-chrome font-semibold">FastAPI (Python 3.13 / Uvicorn)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">EVENT STORAGE</span>
              <span className="text-chrome font-semibold">SQLite (Ephemeral on Render Free Tier)</span>
            </div>
            <div className="p-2.5 bg-background border border-border text-[11px] text-muted leading-relaxed">
              <span className="text-[#d97736] font-bold block uppercase">// PERSISTENCE ADVISORY</span>
              Render free tier uses an ephemeral filesystem. SQLite audit records persist during active sessions and reset upon redeployment or cold shutdown.
            </div>
          </div>
        </div>

        {/* Neural Network Hyperparameters & Structure */}
        <div className="border-industrial bg-surface p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Cpu className="w-4 h-4 text-accent" />
            <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
              NEURAL NETWORK TOPOLOGY
            </h3>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">INPUT DIMENSIONS</span>
              <span className="text-chrome font-semibold">192 encoded features (43 raw flows)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">LAYER ARCHITECTURE</span>
              <span className="text-chrome font-semibold">Linear(192→128) → Linear(128→64) → Linear(64→1)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">REGULARIZATION</span>
              <span className="text-chrome font-semibold">Dropout(0.3 / 0.2), ReLU, Early Stopping</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">TOTAL PARAMETERS</span>
              <span className="text-chrome font-semibold">33,025 trainable weights</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">LOSS FUNCTION</span>
              <span className="text-chrome font-semibold">Binary Cross Entropy with Logits (BCE)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <span className="text-muted">OPTIMIZER</span>
              <span className="text-chrome font-semibold">Adam (lr=0.001, batch_size=256)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Limitations of Benchmark-Based Intrusion Detection */}
      <section className="border-industrial bg-surface p-6">
        <div className="flex items-center gap-2 pb-3 border-b border-border mb-4">
          <AlertTriangle className="w-4 h-4 text-[#d97736]" />
          <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
            BENCHMARK-BASED INTRUSION DETECTION LIMITATIONS
          </h3>
        </div>

        <div className="space-y-3 font-sans text-xs text-muted/90 leading-relaxed">
          <p>
            NØX is currently deployed as an academic mini-project designed for offline evaluation of simulated and recorded network traffic flows.
            Prospective users and evaluators should consider the inherent boundaries of benchmark ML in network security:
          </p>
          <ul className="list-disc list-inside space-y-1.5 pl-2 text-muted">
            <li>
              <strong>Dataset Distribution Shift:</strong> Real-world network protocols evolve continuously. Models trained on the UNSW-NB15 benchmark reflect network distributions specific to synthetic testbed environments.
            </li>
            <li>
              <strong>Offline Batch vs. Live Sniffing:</strong> NØX evaluates pre-aggregated network flow features (durations, packet counts, inter-arrival times). It does not perform inline kernel packet filtering or automated interface blocking.
            </li>
            <li>
              <strong>Adversarial Evasion:</strong> Malicious actors can fragment packets, alter flow intervals, or craft traffic specifically designed to fool neural feature spaces.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
};
