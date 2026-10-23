import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DetectionEvent } from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import {
  History as HistoryIcon,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Shield,
  AlertTriangle,
  FileText,
  X,
  Database,
} from 'lucide-react';

export const History: React.FC = () => {
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination states
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(25);
  const [hasMore, setHasMore] = useState<boolean>(true);

  // Filter states
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string>('all');
  const [predictionFilter, setPredictionFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  // Detail Modal
  const [selectedEvent, setSelectedEvent] = useState<DetectionEvent | null>(null);

  const fetchHistory = async (targetPage: number = page, source?: string) => {
    setIsLoading(true);
    setError(null);
    const offset = (targetPage - 1) * limit;
    const actualSource = source && source !== 'all' ? source : undefined;

    try {
      const data = await api.getHistory(limit, offset, actualSource);
      setEvents(data);
      setHasMore(data.length === limit);
      setPage(targetPage);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch detection audit history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(1, sourceTypeFilter);
  }, [sourceTypeFilter]);

  // Client-side filtering scoped to the loaded batch
  const filteredEvents = events.filter((evt) => {
    if (predictionFilter !== 'all' && evt.prediction !== predictionFilter) return false;
    if (severityFilter !== 'all' && evt.severity !== severityFilter) return false;
    return true;
  });

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'High':
        return 'border-critical/60 bg-critical/10 text-critical';
      case 'Medium':
        return 'border-[#d97736]/60 bg-[#d97736]/10 text-[#d97736]';
      case 'Low':
        return 'border-[#5a7f9e]/60 bg-[#5a7f9e]/10 text-[#5a7f9e]';
      default:
        return 'border-success/60 bg-success/10 text-success';
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-xs uppercase tracking-widest text-accent font-semibold">
              04 // AUDIT STORAGE
            </span>
            <span className="text-muted font-mono text-xs">•</span>
            <span className="font-mono text-xs text-muted">SQLITE EVENT LOGS</span>
          </div>
          <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight text-chrome">
            DETECTION HISTORY
          </h1>
          <p className="font-sans text-sm text-muted mt-2 max-w-2xl">
            Query immutable intrusion audit logs recorded across single, batch, and CSV inference workloads.
          </p>
        </div>

        <button
          onClick={() => fetchHistory(page, sourceTypeFilter)}
          disabled={isLoading}
          className="px-4 py-2 border border-border text-chrome hover:border-chrome text-xs font-mono uppercase tracking-wider flex items-center gap-2 self-start md:self-auto transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>SYNC AUDIT LOG</span>
        </button>
      </div>

      {/* Ephemeral Demo Persistence Notice */}
      <div className="border border-border bg-surface p-4 flex items-start gap-3">
        <Database className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-mono text-xs text-chrome font-bold uppercase tracking-wider">
            <span>DEMO TELEMETRY PERSISTENCE</span>
            <span className="text-[10px] text-muted border border-border px-1.5 py-0.5">SQLITE AUDIT</span>
          </div>
          <p className="font-sans text-xs text-muted leading-relaxed">
            All neural inference results are written to a lightweight SQLite database for review and telemetry aggregation.
            <span className="text-chrome font-semibold"> Hosting Advisory:</span> When deployed on Render's free tier, local disk storage is ephemeral; audit records reset when the instance restarts or spins down from inactivity.
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 border-industrial bg-surface flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-muted text-xs font-mono">
            <Filter className="w-3.5 h-3.5" />
            <span className="uppercase">FILTERS:</span>
          </div>

          {/* Source Type Filter (Server-side supported) */}
          <div className="flex items-center gap-1.5 border border-border px-2.5 py-1 bg-surface-elevated">
            <span className="font-mono text-[10px] uppercase text-muted">SOURCE:</span>
            <select
              value={sourceTypeFilter}
              onChange={(e) => setSourceTypeFilter(e.target.value)}
              className="bg-transparent text-chrome font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="all">ALL SOURCES</option>
              <option value="csv_upload">CSV UPLOAD</option>
              <option value="single">SINGLE API</option>
              <option value="batch">BATCH API</option>
            </select>
          </div>

          {/* Prediction Filter (Client-scoped to batch) */}
          <div className="flex items-center gap-1.5 border border-border px-2.5 py-1 bg-surface-elevated">
            <span className="font-mono text-[10px] uppercase text-muted">PREDICTION:</span>
            <select
              value={predictionFilter}
              onChange={(e) => setPredictionFilter(e.target.value)}
              className="bg-transparent text-chrome font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="all">ALL</option>
              <option value="Normal">NORMAL</option>
              <option value="Malicious">MALICIOUS</option>
            </select>
          </div>

          {/* Severity Filter (Client-scoped to batch) */}
          <div className="flex items-center gap-1.5 border border-border px-2.5 py-1 bg-surface-elevated">
            <span className="font-mono text-[10px] uppercase text-muted">SEVERITY:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-chrome font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="all">ALL</option>
              <option value="Normal">NORMAL</option>
              <option value="Low">LOW</option>
              <option value="Medium">MEDIUM</option>
              <option value="High">HIGH</option>
            </select>
          </div>
        </div>

        <span className="font-mono text-xs text-muted">
          Showing {filteredEvents.length} records in current page
        </span>
      </div>

      {/* Main Content Area */}
      {isLoading && events.length === 0 ? (
        <LoadingState message="FETCHING HISTORICAL AUDIT ENTRIES..." />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchHistory(page, sourceTypeFilter)} />
      ) : events.length === 0 ? (
        <EmptyState
          title="NO AUDIT RECORDS FOUND"
          message="No historical detection events exist in the database for the selected criteria."
          actionLabel="EXECUTE INFERENCE SCAN"
          actionPath="/detect"
        />
      ) : (
        <div className="border-industrial bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-elevated font-mono text-[11px] uppercase tracking-wider text-muted">
                  <th className="py-3 px-4">EVENT ID</th>
                  <th className="py-3 px-4">TIMESTAMP</th>
                  <th className="py-3 px-4">PREDICTION</th>
                  <th className="py-3 px-4">ATTACK SCORE</th>
                  <th className="py-3 px-4">SEVERITY</th>
                  <th className="py-3 px-4">SOURCE</th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-xs">
                {filteredEvents.map((evt) => {
                  const isMalicious = evt.prediction === 'Malicious' || evt.class_id === 1;
                  return (
                    <tr
                      key={evt.id}
                      className="hover:bg-surface-elevated/70 transition-colors group cursor-pointer"
                      onClick={() => setSelectedEvent(evt)}
                    >
                      <td className="py-3 px-4 text-chrome font-bold">
                        #{evt.id.toString().padStart(5, '0')}
                      </td>
                      <td className="py-3 px-4 text-chrome whitespace-nowrap">
                        {new Date(evt.timestamp).toLocaleString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {isMalicious ? (
                            <>
                              <AlertTriangle className="w-3.5 h-3.5 text-accent shrink-0" />
                              <span className="text-accent font-semibold tracking-wide uppercase">
                                MALICIOUS
                              </span>
                            </>
                          ) : (
                            <>
                              <Shield className="w-3.5 h-3.5 text-success shrink-0" />
                              <span className="text-success tracking-wide uppercase">NORMAL</span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-background border border-border">
                            <div
                              className={`h-full ${isMalicious ? 'bg-accent' : 'bg-success'}`}
                              style={{ width: `${Math.min(100, Math.max(0, evt.attack_score * 100))}%` }}
                            />
                          </div>
                          <span>{(evt.attack_score * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 border text-[10px] uppercase font-bold tracking-wider ${getSeverityBadgeClass(
                            evt.severity
                          )}`}
                        >
                          {evt.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-muted text-[11px] uppercase">
                        {evt.source_type}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-xs text-muted group-hover:text-chrome transition-colors">
                          VIEW →
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="p-4 border-t border-border flex items-center justify-between font-mono text-xs">
            <span className="text-muted">
              PAGE {page} (LIMIT: {limit} EVENTS / FETCH)
            </span>

            <div className="flex items-center gap-3">
              <button
                onClick={() => fetchHistory(page - 1, sourceTypeFilter)}
                disabled={page <= 1 || isLoading}
                className="px-3 py-1.5 border border-border text-muted hover:text-chrome hover:border-chrome disabled:opacity-30 transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>PREV</span>
              </button>

              <button
                onClick={() => fetchHistory(page + 1, sourceTypeFilter)}
                disabled={!hasMore || isLoading}
                className="px-3 py-1.5 border border-border text-muted hover:text-chrome hover:border-chrome disabled:opacity-30 transition-colors flex items-center gap-1"
              >
                <span>NEXT</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Event Inspection Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="border-industrial bg-surface max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-chrome" />
                <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
                  AUDIT EVENT DETAIL #{selectedEvent.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-muted hover:text-chrome p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">EVENT ID:</span>
                <span className="text-chrome font-bold">#{selectedEvent.id}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">TIMESTAMP (LOCAL):</span>
                <span className="text-chrome">
                  {new Date(selectedEvent.timestamp).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">PREDICTION:</span>
                <span
                  className={
                    selectedEvent.prediction === 'Malicious' ? 'text-accent font-bold' : 'text-success font-bold'
                  }
                >
                  {selectedEvent.prediction.toUpperCase()} (Class {selectedEvent.class_id})
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">ATTACK PROBABILITY:</span>
                <span className="text-chrome font-bold">
                  {(selectedEvent.attack_score * 100).toFixed(4)}% ({selectedEvent.attack_score})
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">DECISION THRESHOLD:</span>
                <span className="text-chrome">{selectedEvent.threshold}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">SEVERITY LEVEL:</span>
                <span
                  className={`px-2 py-0.5 border text-[10px] uppercase font-bold ${getSeverityBadgeClass(
                    selectedEvent.severity
                  )}`}
                >
                  {selectedEvent.severity}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">MODEL VERSION:</span>
                <span className="text-chrome">{selectedEvent.model_version}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-border/50">
                <span className="text-muted uppercase">DETECTION SOURCE:</span>
                <span className="text-chrome uppercase">{selectedEvent.source_type}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 bg-surface-elevated border border-border text-xs font-mono uppercase text-chrome hover:border-chrome transition-colors"
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
