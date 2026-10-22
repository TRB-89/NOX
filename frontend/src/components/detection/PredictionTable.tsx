import React, { useState } from 'react';
import { DetectionResult } from '../../types';
import { Shield, AlertTriangle, ArrowUpDown, ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react';

interface PredictionTableProps {
  predictions: DetectionResult[];
  title?: string;
  isHistory?: boolean;
}

export const PredictionTable: React.FC<PredictionTableProps> = ({
  predictions,
  title = 'FLOW INFERENCE PREVIEWS',
  isHistory = false,
}) => {
  const [filter, setFilter] = useState<'all' | 'Normal' | 'Malicious'>('all');
  const [severityFilter, setSeverityFilter] = useState<'all' | 'Normal' | 'Low' | 'Medium' | 'High'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const filteredPredictions = predictions.filter((p) => {
    if (filter !== 'all' && p.prediction !== filter) return false;
    if (severityFilter !== 'all' && p.severity !== severityFilter) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filteredPredictions.length / pageSize));
  const displayedPredictions = filteredPredictions.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

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
    <div className="border-industrial bg-surface p-6">
      {/* Header and Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h3 className="font-display text-sm font-bold uppercase tracking-tight text-chrome">
            {title}
          </h3>
          <p className="font-sans text-xs text-muted mt-0.5">
            Individual flow predictions from PyTorch neural classifier with attack scoring.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 border border-border px-2 py-1 bg-surface-elevated">
            <SlidersHorizontal className="w-3 h-3 text-muted" />
            <span className="font-mono text-[10px] uppercase text-muted">PREDICTION:</span>
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="bg-transparent text-chrome font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value="all">ALL ({predictions.length})</option>
              <option value="Normal">NORMAL</option>
              <option value="Malicious">MALICIOUS</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 border border-border px-2 py-1 bg-surface-elevated">
            <span className="font-mono text-[10px] uppercase text-muted">SEVERITY:</span>
            <select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value as any);
                setCurrentPage(1);
              }}
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
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto mt-4">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-elevated font-mono text-[11px] uppercase tracking-wider text-muted">
              <th className="py-2.5 px-3">#</th>
              <th className="py-2.5 px-3">TIMESTAMP</th>
              <th className="py-2.5 px-3">CLASSIFICATION</th>
              <th className="py-2.5 px-3">ATTACK SCORE</th>
              <th className="py-2.5 px-3">SEVERITY</th>
              <th className="py-2.5 px-3">MODEL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border font-mono text-xs">
            {displayedPredictions.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-muted font-sans text-xs">
                  No records match current filters.
                </td>
              </tr>
            ) : (
              displayedPredictions.map((pred, index) => {
                const isMalicious = pred.prediction === 'Malicious' || pred.class_id === 1;
                const scorePercent = (pred.attack_score * 100).toFixed(1);
                const actualIndex = (currentPage - 1) * pageSize + index + 1;

                return (
                  <tr
                    key={index}
                    className="hover:bg-surface-elevated/70 transition-colors group"
                  >
                    <td className="py-3 px-3 text-muted">{actualIndex.toString().padStart(2, '0')}</td>
                    <td className="py-3 px-3 text-chrome whitespace-nowrap">
                      {new Date(pred.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                      <span className="text-muted block text-[10px]">
                        {new Date(pred.timestamp).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-3 px-3">
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
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-background border border-border overflow-hidden">
                          <div
                            className={`h-full ${
                              isMalicious ? 'bg-accent' : 'bg-success'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, pred.attack_score * 100))}%` }}
                          />
                        </div>
                        <span className="text-chrome font-medium">
                          {scorePercent}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 border text-[10px] uppercase font-bold tracking-wider ${getSeverityBadgeClass(
                          pred.severity
                        )}`}
                      >
                        {pred.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-muted text-[11px] whitespace-nowrap">
                      {pred.model || 'NØX-MLP-v1'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 mt-2 border-t border-border">
          <span className="font-mono text-xs text-muted">
            Showing {(currentPage - 1) * pageSize + 1}-
            {Math.min(currentPage * pageSize, filteredPredictions.length)} of{' '}
            {filteredPredictions.length} records
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 border border-border text-muted hover:text-chrome hover:border-chrome disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-xs text-chrome px-2">
              PAGE {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 border border-border text-muted hover:text-chrome hover:border-chrome disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
