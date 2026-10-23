import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'SYSTEM TELEMETRY ERROR',
  message = 'Failed to connect to the NØX FastAPI backend.',
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-accent/40 bg-surface my-6">
      <div className="p-3 border border-accent/60 mb-4 bg-background">
        <AlertTriangle className="w-8 h-8 text-accent animate-pulse" />
      </div>
      <h3 className="font-mono text-sm tracking-widest text-chrome uppercase font-semibold">
        {title}
      </h3>
      <p className="font-sans text-xs text-muted max-w-lg mt-2 leading-relaxed">
        {message}
      </p>

      {/* Cloud Diagnostic Help */}
      <div className="mt-5 p-3.5 bg-background border border-border max-w-md text-left font-mono text-[11px] text-muted space-y-1.5">
        <span className="text-chrome font-bold uppercase block tracking-wider">// CLOUD HOSTING DIAGNOSTICS</span>
        <p className="text-muted/90">• <strong className="text-chrome">Cold Starts:</strong> On Render Free Tier, servers sleep after 15 min idle. Initial spin-up requires ~60-90 seconds.</p>
        <p className="text-muted/90">• <strong className="text-chrome">Environment:</strong> Verify <span className="text-accent">VITE_API_BASE_URL</span> points to your live Render backend URL in Vercel.</p>
        <p className="text-muted/90">• <strong className="text-chrome">CORS:</strong> Ensure your Vercel URL is allowed by backend CORS settings.</p>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 flex items-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          RETRY CONNECTION
        </button>
      )}
    </div>
  );
};
