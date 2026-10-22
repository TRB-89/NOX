import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ShieldAlert, ShieldCheck, Flame, ArrowRight, RefreshCw, Cpu } from 'lucide-react';
import { api } from '../services/api';
import { TelemetryStats, DetectionEvent } from '../types';
import { StatCard } from '../components/dashboard/StatCard';
import { TrafficChart } from '../components/dashboard/TrafficChart';
import { SeverityChart } from '../components/dashboard/SeverityChart';
import { RecentAlerts } from '../components/dashboard/RecentAlerts';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const Overview: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [recentEvents, setRecentEvents] = useState<DetectionEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsRes, historyRes] = await Promise.all([
        api.getStats(),
        api.getHistory(10, 0),
      ]);
      setStats(statsRes);
      setRecentEvents(historyRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load telemetry overview.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (isLoading && !stats) {
    return <LoadingState message="ACQUIRING NEURAL METRICS & AUDIT LOGS..." />;
  }

  if (error && !stats) {
    return <ErrorState message={error} onRetry={fetchDashboardData} />;
  }

  const highSeverityCount = stats?.severity_distribution?.High ?? 0;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-industrial bg-surface p-8 md:p-12">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-96 h-96 opacity-10 pointer-events-none">
          {/* Decorative Neural Network SVG */}
          <svg viewBox="0 0 400 400" className="w-full h-full text-chrome stroke-current">
            <circle cx="80" cy="100" r="8" fill="currentColor" />
            <circle cx="80" cy="200" r="8" fill="currentColor" />
            <circle cx="80" cy="300" r="8" fill="currentColor" />
            <circle cx="200" cy="70" r="8" fill="currentColor" />
            <circle cx="200" cy="160" r="8" fill="currentColor" />
            <circle cx="200" cy="250" r="8" fill="currentColor" />
            <circle cx="200" cy="340" r="8" fill="currentColor" />
            <circle cx="320" cy="140" r="8" fill="currentColor" />
            <circle cx="320" cy="260" r="8" fill="currentColor" />
            <line x1="80" y1="100" x2="200" y2="70" strokeWidth="1" strokeDasharray="4 2" />
            <line x1="80" y1="100" x2="200" y2="160" strokeWidth="1" />
            <line x1="80" y1="200" x2="200" y2="160" strokeWidth="1" />
            <line x1="80" y1="200" x2="200" y2="250" strokeWidth="1" strokeDasharray="3 3" />
            <line x1="80" y1="300" x2="200" y2="250" strokeWidth="1" />
            <line x1="80" y1="300" x2="200" y2="340" strokeWidth="1" />
            <line x1="200" y1="70" x2="320" y2="140" strokeWidth="1" />
            <line x1="200" y1="160" x2="320" y2="140" strokeWidth="1" />
            <line x1="200" y1="250" x2="320" y2="260" strokeWidth="1" strokeDasharray="5 2" />
            <line x1="200" y1="340" x2="320" y2="260" strokeWidth="1" />
          </svg>
        </div>

        <div className="relative z-10 max-w-2xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="font-mono text-xs uppercase tracking-widest text-accent font-semibold">
              // INTELLIGENCE IN THE DARK
            </span>
            <span className="text-muted font-mono text-xs">•</span>
            <span className="font-mono text-xs text-muted">MODULE 04</span>
          </div>

          <h1 className="font-display text-4xl md:text-5xl font-extrabold uppercase tracking-tight text-chrome leading-none">
            NØX
          </h1>
          <p className="font-display text-sm md:text-base uppercase tracking-widest text-muted mt-2">
            NEURAL NETWORK INTRUSION DETECTION
          </p>

          <p className="font-sans text-sm md:text-base text-muted/80 mt-4 leading-relaxed">
            Analyze network traffic. Identify anomalies. Detect potential intrusions using deep
            multilayer perceptron inference trained on the UNSW-NB15 benchmark.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <button
              onClick={() => navigate('/detect')}
              className="px-6 py-3 bg-accent hover:bg-accent-hover text-white font-mono text-xs uppercase tracking-wider font-semibold transition-colors flex items-center gap-2.5 shadow-sm"
            >
              <span>START DETECTION →</span>
            </button>

            <button
              onClick={() => fetchDashboardData()}
              className="px-4 py-3 border border-border hover:border-chrome text-chrome font-mono text-xs uppercase tracking-wider transition-colors flex items-center gap-2"
              title="Refresh telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5 text-muted" />
              <span>SYNC TELEMETRY</span>
            </button>
          </div>
        </div>
      </section>

      {/* Metric Cards Grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-xs font-bold uppercase tracking-widest text-muted">
            01 // CORE TELEMETRY METRICS
          </h2>
          {stats?.most_recent_detection_timestamp && (
            <span className="font-mono text-[11px] text-muted">
              Last Detection: {new Date(stats.most_recent_detection_timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Records Analyzed"
            value={stats?.total_records_analyzed ?? 0}
            icon={Database}
            subtitle="Logged flows in SQLite"
          />
          <StatCard
            title="Potential Attacks Detected"
            value={stats?.predicted_malicious_count ?? 0}
            icon={ShieldAlert}
            subtitle={
              stats && stats.total_records_analyzed > 0
                ? `${stats.attack_percentage.toFixed(2)}% malicious ratio`
                : 'No attacks recorded'
            }
            tone={stats && stats.predicted_malicious_count > 0 ? 'accent' : 'default'}
          />
          <StatCard
            title="Normal Traffic Records"
            value={stats?.predicted_normal_count ?? 0}
            icon={ShieldCheck}
            subtitle="Verified benign flows"
            tone="success"
          />
          <StatCard
            title="High-Severity Alerts"
            value={highSeverityCount}
            icon={Flame}
            subtitle="Probability score ≥ 0.90"
            tone={highSeverityCount > 0 ? 'critical' : 'default'}
          />
        </div>
      </section>

      {/* Visualizations Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrafficChart
          normalCount={stats?.predicted_normal_count ?? 0}
          maliciousCount={stats?.predicted_malicious_count ?? 0}
        />
        <SeverityChart
          severityDistribution={
            stats?.severity_distribution ?? { Normal: 0, Low: 0, Medium: 0, High: 0 }
          }
        />
      </section>

      {/* Recent Activity Table */}
      <section>
        <RecentAlerts events={recentEvents} />
      </section>
    </div>
  );
};
