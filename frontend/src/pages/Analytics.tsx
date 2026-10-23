import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import { api } from '../services/api';
import { TelemetryStats, DetectionEvent } from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { BarChart3, PieChart as PieIcon, ShieldAlert, Award, AlertCircle, Info } from 'lucide-react';
import { useBackend } from '../services/BackendContext';

export const Analytics: React.FC = () => {
  const { refreshKey, retryConnection, isChecking } = useBackend();
  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyticsData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsRes, historyRes] = await Promise.all([
        api.getStats(),
        api.getHistory(100, 0),
      ]);
      setStats(statsRes);
      setEvents(historyRes);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve telemetry analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [refreshKey]);

  const handleRetry = async () => {
    await retryConnection();
    await fetchAnalyticsData();
  };

  if (isLoading) {
    return <LoadingState message="COMPUTING THREAT ANALYTICS & HISTOGRAMS..." />;
  }

  if (error && !stats) {
    return (
      <ErrorState
        message={error}
        onRetry={handleRetry}
        isRetrying={isChecking}
      />
    );
  }

  const hasData = (stats?.total_records_analyzed ?? 0) > 0;

  // Traffic Ratio Data
  const trafficData = [
    { name: 'NORMAL', count: stats?.predicted_normal_count ?? 0, color: '#79a995' },
    { name: 'MALICIOUS', count: stats?.predicted_malicious_count ?? 0, color: '#a62735' },
  ];

  // Severity Distribution Data
  const severityData = [
    { name: 'NORMAL', count: stats?.severity_distribution?.Normal ?? 0, color: '#79a995' },
    { name: 'LOW', count: stats?.severity_distribution?.Low ?? 0, color: '#5a7f9e' },
    { name: 'MEDIUM', count: stats?.severity_distribution?.Medium ?? 0, color: '#d97736' },
    { name: 'HIGH', count: stats?.severity_distribution?.High ?? 0, color: '#db3346' },
  ];

  // Compute Attack Score Bins from loaded detection events (0.0 to 1.0)
  const scoreBins = [
    { range: '0.0 - 0.2', count: 0 },
    { range: '0.2 - 0.4', count: 0 },
    { range: '0.4 - 0.6', count: 0 },
    { range: '0.6 - 0.8', count: 0 },
    { range: '0.8 - 1.0', count: 0 },
  ];

  events.forEach((evt) => {
    const s = evt.attack_score;
    if (s < 0.2) scoreBins[0].count++;
    else if (s < 0.4) scoreBins[1].count++;
    else if (s < 0.6) scoreBins[2].count++;
    else if (s < 0.8) scoreBins[3].count++;
    else scoreBins[4].count++;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div className="border-b border-border pb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-xs uppercase tracking-widest text-accent font-semibold">
            03 // THREAT ANALYTICS
          </span>
          <span className="text-muted font-mono text-xs">•</span>
          <span className="font-mono text-xs text-muted">DISTRIBUTION & BENCHMARKS</span>
        </div>
        <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight text-chrome">
          THREAT ANALYTICS
        </h1>
        <p className="font-sans text-sm text-muted mt-2 max-w-2xl">
          Empirical classification telemetry derived from live inference operations and audited flow events.
        </p>
      </div>

      {!hasData ? (
        <EmptyState
          title="NO DETECTION TELEMETRY RECORDED"
          message="Run an inference scan via the Neural Detection page to populate analytical telemetry."
          actionLabel="RUN NEURAL DETECTION →"
          actionPath="/detect"
        />
      ) : (
        <>
          {/* Charts Row 1: Traffic Breakdown and Severity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Traffic Ratio Donut / Bar */}
            <div className="border-industrial bg-surface p-6">
              <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
                <div>
                  <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
                    NORMAL VS. MALICIOUS RATIO
                  </h3>
                  <p className="font-sans text-xs text-muted mt-0.5">
                    Proportion of identified network threats versus benign traffic.
                  </p>
                </div>
                <PieIcon className="w-4 h-4 text-muted" />
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={trafficData}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={85}
                      stroke="#101010"
                      strokeWidth={3}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    >
                      {trafficData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101010',
                        borderColor: '#292929',
                        borderRadius: 0,
                        color: '#dedede',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="flex justify-around pt-2 border-t border-border font-mono text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 bg-success" />
                  <span className="text-muted">NORMAL:</span>
                  <span className="text-chrome font-bold">
                    {stats?.predicted_normal_count.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 bg-accent" />
                  <span className="text-muted">MALICIOUS:</span>
                  <span className="text-accent font-bold">
                    {stats?.predicted_malicious_count.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Severity Distribution */}
            <div className="border-industrial bg-surface p-6">
              <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
                <div>
                  <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
                    THREAT SEVERITY BREAKDOWN
                  </h3>
                  <p className="font-sans text-xs text-muted mt-0.5">
                    Classification categorized by model output confidence levels.
                  </p>
                </div>
                <BarChart3 className="w-4 h-4 text-muted" />
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={severityData} margin={{ top: 20, right: 10, left: -20, bottom: 5 }}>
                    <XAxis
                      dataKey="name"
                      stroke="#888888"
                      fontSize={11}
                      tickLine={false}
                      fontFamily="monospace"
                    />
                    <YAxis stroke="#888888" fontSize={11} tickLine={false} fontFamily="monospace" />
                    <Tooltip
                      cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                      contentStyle={{
                        backgroundColor: '#101010',
                        borderColor: '#292929',
                        borderRadius: 0,
                        color: '#dedede',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 0, 0, 0]}>
                      {severityData.map((entry, index) => (
                        <Cell key={`bar-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-border font-mono text-[11px] text-center">
                <div>
                  <span className="text-muted block text-[10px]">NORMAL</span>
                  <span className="text-chrome font-bold">{severityData[0].count}</span>
                </div>
                <div>
                  <span className="text-muted block text-[10px]">LOW</span>
                  <span className="text-chrome font-bold">{severityData[1].count}</span>
                </div>
                <div>
                  <span className="text-muted block text-[10px]">MEDIUM</span>
                  <span className="text-chrome font-bold">{severityData[2].count}</span>
                </div>
                <div>
                  <span className="text-muted block text-[10px]">HIGH</span>
                  <span className="text-critical font-bold">{severityData[3].count}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Row 2: Attack Score Distribution Histogram */}
          <div className="border-industrial bg-surface p-6">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
              <div>
                <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
                  NEURAL ATTACK SCORE DISTRIBUTION
                </h3>
                <p className="font-sans text-xs text-muted mt-0.5">
                  Histogram of sigmoid probabilities across recent {events.length} audited flow events.
                </p>
              </div>
              <ShieldAlert className="w-4 h-4 text-muted" />
            </div>

            {events.length === 0 ? (
              <div className="py-12 text-center text-muted font-mono text-xs">
                Score distribution unavailable: no logged history events found.
              </div>
            ) : (
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scoreBins} margin={{ top: 20, right: 10, left: -20, bottom: 5 }}>
                    <XAxis
                      dataKey="range"
                      stroke="#888888"
                      fontSize={11}
                      tickLine={false}
                      fontFamily="monospace"
                    />
                    <YAxis stroke="#888888" fontSize={11} tickLine={false} fontFamily="monospace" />
                    <Tooltip
                      cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                      contentStyle={{
                        backgroundColor: '#101010',
                        borderColor: '#292929',
                        borderRadius: 0,
                        color: '#dedede',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#dedede" radius={[0, 0, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}

      {/* Model Performance Panel (Module 2 Offline Benchmark) */}
      <section className="border-industrial bg-surface p-6">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-accent" />
              <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
                OFFLINE BENCHMARK EVALUATION (MODULE 02)
              </h3>
            </div>
            <p className="font-sans text-xs text-muted mt-0.5">
              Trained PyTorch Multilayer Perceptron metrics on the held-out UNSW-NB15 test partition (82,332 records).
            </p>
          </div>
          <span className="font-mono text-[10px] uppercase border border-border px-2 py-0.5 text-muted">
            OFFLINE BENCHMARK ONLY
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 font-mono">
          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">ACCURACY</span>
            <span className="text-xl font-bold text-chrome">85.69%</span>
          </div>

          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">RECALL (MALICIOUS)</span>
            <span className="text-xl font-bold text-success">97.73%</span>
          </div>

          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">PRECISION</span>
            <span className="text-xl font-bold text-chrome">80.47%</span>
          </div>

          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">F1-SCORE</span>
            <span className="text-xl font-bold text-chrome">88.27%</span>
          </div>

          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">FALSE POSITIVE RATE</span>
            <span className="text-xl font-bold text-accent">29.05%</span>
          </div>

          <div className="p-3 bg-surface-elevated border border-border">
            <span className="text-[10px] text-muted uppercase block">ROC-AUC SCORE</span>
            <span className="text-xl font-bold text-chrome">0.9757</span>
          </div>
        </div>

        <div className="mt-4 p-3 bg-surface-elevated border border-border flex items-start gap-2.5 text-xs text-muted font-sans">
          <Info className="w-4 h-4 text-chrome shrink-0 mt-0.5" />
          <span>
            <strong>Benchmark Disclaimer:</strong> These metrics reflect supervised evaluation on pre-recorded benchmark data
            (Module 02: <code>nox_mlp.pth</code>). Real-world network detection depends on protocol distributions and traffic symmetry.
          </span>
        </div>
      </section>
    </div>
  );
};
