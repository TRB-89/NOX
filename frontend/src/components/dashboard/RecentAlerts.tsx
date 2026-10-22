import React from 'react';
import { DetectionEvent } from '../../types';
import { ShieldAlert, ShieldCheck } from 'lucide-react';

interface RecentAlertsProps {
  events: DetectionEvent[];
}

export const RecentAlerts: React.FC<RecentAlertsProps> = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className="border-industrial bg-surface p-5 text-center text-muted font-mono text-xs">
        NO RECENT DETECTION INCIDENTS RECORDED
      </div>
    );
  }

  const formatTimestamp = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'High':
        return 'text-accent border-accent/60 bg-accent/10';
      case 'Medium':
        return 'text-orange-400 border-orange-500/40 bg-orange-500/10';
      case 'Low':
        return 'text-chrome border-border bg-surface-elevated';
      default:
        return 'text-success border-success/40 bg-success/10';
    }
  };

  return (
    <div className="border-industrial bg-surface p-5">
      <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
        <h3 className="font-mono text-xs uppercase tracking-widest text-chrome font-semibold">
          RECENT DETECTION EVENTS
        </h3>
        <span className="font-mono text-[10px] text-muted">
          LATEST {events.length} LOGS
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-border text-muted text-[10px] uppercase tracking-wider">
              <th className="pb-2.5 font-normal">Event ID</th>
              <th className="pb-2.5 font-normal">Time</th>
              <th className="pb-2.5 font-normal">Classification</th>
              <th className="pb-2.5 font-normal">Attack Score</th>
              <th className="pb-2.5 font-normal">Severity</th>
              <th className="pb-2.5 font-normal">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {events.map((evt) => {
              const isAttack = evt.class_id === 1;
              return (
                <tr key={evt.id} className="hover:bg-surface-elevated transition-colors">
                  <td className="py-2.5 text-muted">#{evt.id}</td>
                  <td className="py-2.5 text-chrome">{formatTimestamp(evt.timestamp)}</td>
                  <td className="py-2.5">
                    <span className="flex items-center gap-1.5 font-semibold">
                      {isAttack ? (
                        <>
                          <ShieldAlert className="w-3.5 h-3.5 text-accent" />
                          <span className="text-accent">{evt.prediction}</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3.5 h-3.5 text-success" />
                          <span className="text-success">{evt.prediction}</span>
                        </>
                      )}
                    </span>
                  </td>
                  <td className="py-2.5 text-chrome font-semibold">
                    {(evt.attack_score * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5">
                    <span
                      className={`inline-block px-1.5 py-0.5 text-[10px] uppercase border font-semibold ${getSeverityBadge(
                        evt.severity
                      )}`}
                    >
                      {evt.severity}
                    </span>
                  </td>
                  <td className="py-2.5 text-muted uppercase text-[10px]">
                    {evt.source_type}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
