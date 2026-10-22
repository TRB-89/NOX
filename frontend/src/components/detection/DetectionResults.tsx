import React from 'react';
import { CSVUploadResponse } from '../../types';
import { ShieldCheck, AlertTriangle, Activity, Database, CheckCircle, Info } from 'lucide-react';

interface DetectionResultsProps {
  results: CSVUploadResponse;
  onReset?: () => void;
}

export const DetectionResults: React.FC<DetectionResultsProps> = ({ results, onReset }) => {
  const {
    total_records_analyzed,
    normal_traffic_count,
    potential_attack_count,
    attack_percentage,
    severity_distribution,
    preview_predictions,
    preview_limit,
  } = results;

  const isHighRisk = attack_percentage > 20;

  return (
    <div className="border-industrial bg-surface p-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-3">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse" />
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-muted block">
              STATUS
            </span>
            <h3 className="font-display text-lg font-bold uppercase tracking-tight text-chrome">
              DETECTION COMPLETE
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="font-mono text-xs text-muted border border-border px-2.5 py-1">
            PREVIEW RECORD LIMIT: {preview_limit}
          </span>
          {onReset && (
            <button
              onClick={onReset}
              className="px-3 py-1 border border-border text-xs font-mono uppercase text-muted hover:text-chrome hover:border-chrome transition-colors"
            >
              NEW SCAN
            </button>
          )}
        </div>
      </div>

      {/* Metric Breakdown Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Analyzed */}
        <div className="p-4 bg-surface-elevated border border-border">
          <div className="flex items-center justify-between text-muted mb-1">
            <span className="font-mono text-[10px] uppercase tracking-wider">TOTAL ANALYZED</span>
            <Database className="w-3.5 h-3.5" />
          </div>
          <div className="font-mono text-2xl font-bold text-chrome">
            {total_records_analyzed.toLocaleString()}
          </div>
          <div className="font-sans text-[11px] text-muted mt-1">Network traffic flows</div>
        </div>

        {/* Normal Traffic */}
        <div className="p-4 bg-surface-elevated border border-border">
          <div className="flex items-center justify-between text-success mb-1">
            <span className="font-mono text-[10px] uppercase tracking-wider">PREDICTED NORMAL</span>
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <div className="font-mono text-2xl font-bold text-success">
            {normal_traffic_count.toLocaleString()}
          </div>
          <div className="font-sans text-[11px] text-muted mt-1">
            {total_records_analyzed > 0
              ? `${((normal_traffic_count / total_records_analyzed) * 100).toFixed(1)}% safe`
              : '0% safe'}
          </div>
        </div>

        {/* Malicious Detections */}
        <div className="p-4 bg-surface-elevated border border-border">
          <div className="flex items-center justify-between text-accent mb-1">
            <span className="font-mono text-[10px] uppercase tracking-wider">POTENTIAL ATTACKS</span>
            <AlertTriangle className="w-3.5 h-3.5" />
          </div>
          <div className="font-mono text-2xl font-bold text-accent">
            {potential_attack_count.toLocaleString()}
          </div>
          <div className="font-sans text-[11px] text-muted mt-1">
            {attack_percentage.toFixed(2)}% malicious ratio
          </div>
        </div>

        {/* Threat Level */}
        <div className="p-4 bg-surface-elevated border border-border">
          <div className="flex items-center justify-between text-muted mb-1">
            <span className="font-mono text-[10px] uppercase tracking-wider">THREAT LEVEL</span>
            <Activity className="w-3.5 h-3.5" />
          </div>
          <div
            className={`font-mono text-2xl font-bold ${
              isHighRisk ? 'text-critical' : potential_attack_count > 0 ? 'text-accent' : 'text-success'
            }`}
          >
            {isHighRisk ? 'ELEVATED' : potential_attack_count > 0 ? 'GUARDED' : 'NOMINAL'}
          </div>
          <div className="font-sans text-[11px] text-muted mt-1">
            {potential_attack_count > 0 ? 'Threat signatures detected' : 'Zero malicious vectors'}
          </div>
        </div>
      </div>

      {/* Severity Breakdown Bar */}
      <div className="p-4 bg-surface-elevated border border-border space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs uppercase tracking-wider text-chrome font-semibold">
            SEVERITY DISTRIBUTION BREAKDOWN
          </span>
          <span className="font-mono text-[11px] text-muted">
            Source: PyTorch Neural Classifier
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          <div className="border-l-2 border-success pl-3">
            <span className="font-mono text-[10px] uppercase text-muted block">NORMAL</span>
            <span className="font-mono text-base font-bold text-chrome">
              {severity_distribution.Normal.toLocaleString()}
            </span>
          </div>
          <div className="border-l-2 border-[#5a7f9e] pl-3">
            <span className="font-mono text-[10px] uppercase text-muted block">LOW</span>
            <span className="font-mono text-base font-bold text-chrome">
              {severity_distribution.Low.toLocaleString()}
            </span>
          </div>
          <div className="border-l-2 border-[#d97736] pl-3">
            <span className="font-mono text-[10px] uppercase text-muted block">MEDIUM</span>
            <span className="font-mono text-base font-bold text-chrome">
              {severity_distribution.Medium.toLocaleString()}
            </span>
          </div>
          <div className="border-l-2 border-critical pl-3">
            <span className="font-mono text-[10px] uppercase text-muted block">HIGH</span>
            <span className="font-mono text-base font-bold text-critical">
              {severity_distribution.High.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Note about preview limitations */}
      <div className="flex items-center gap-2 p-3 bg-background/60 border border-border text-xs font-mono text-muted">
        <Info className="w-4 h-4 text-chrome shrink-0" />
        <span>
          Showing initial preview of {preview_predictions.length} flows. All {total_records_analyzed.toLocaleString()}{' '}
          records have been logged to the NØX SQLite audit storage for historical indexing.
        </span>
      </div>
    </div>
  );
};
