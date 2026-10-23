import React from 'react';
import { AlertTriangle, RefreshCw, Server, WifiOff } from 'lucide-react';
import { api } from '../../services/api';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'SYSTEM TELEMETRY ERROR',
  message = 'Failed to connect to the NØX FastAPI backend.',
  onRetry,
  isRetrying = false,
}) => {
  const currentBaseUrl = typeof api?.getBaseUrl === 'function' ? api.getBaseUrl() : 'http://127.0.0.1:8000';
  const isLocal = typeof api?.isLocalhost === 'function' ? api.isLocalhost() : true;

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-accent/40 bg-surface my-6 animate-fade-in">
      <div className="p-3 border border-accent/60 mb-4 bg-background">
        <AlertTriangle className="w-8 h-8 text-accent animate-pulse" />
      </div>
      <h3 className="font-mono text-sm tracking-widest text-chrome uppercase font-semibold">
        {title}
      </h3>
      <p className="font-sans text-xs text-muted max-w-lg mt-2 leading-relaxed">
        {message}
      </p>

      {/* Target Backend Endpoint Badge */}
      <div className="mt-4 px-3 py-1.5 bg-background border border-border font-mono text-[11px] text-muted flex items-center gap-2">
        <Server className="w-3.5 h-3.5 text-chrome" />
        <span>TARGET BACKEND:</span>
        <span className="text-chrome font-semibold">{currentBaseUrl}</span>
      </div>

      {/* Cloud Diagnostic Help */}
      <div className="mt-4 p-3.5 bg-background border border-border max-w-md text-left font-mono text-[11px] text-muted space-y-1.5">
        <span className="text-chrome font-bold uppercase block tracking-wider">// CLOUD HOSTING DIAGNOSTICS</span>
        <p className="text-muted/90">
          • <strong className="text-chrome">Render Free Tier:</strong> Services sleep after 15 minutes of inactivity. First spin-up takes 60–90 seconds.
        </p>
        <p className="text-muted/90">
          • <strong className="text-chrome">Environment Variable:</strong> Ensure <span className="text-accent">VITE_API_BASE_URL</span> in Vercel points to your live Render HTTPS URL.
        </p>
        <p className="text-muted/90">
          • <strong className="text-chrome">CORS Policy:</strong> Render must have <span className="text-accent">CORS_ORIGIN_REGEX</span> configured to permit Vercel domains.
        </p>
        {isLocal && typeof window !== 'undefined' && window.location.hostname !== 'localhost' && (
          <p className="text-critical font-semibold">
            • <strong className="text-critical">Warning:</strong> Active target URL is localhost on a remote deployment. Set VITE_API_BASE_URL in Vercel to your live Render backend URL.
          </p>
        )}
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          disabled={isRetrying}
          className="mt-6 flex items-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-60 text-white text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
          <span>{isRetrying ? 'RECONNECTING...' : 'RETRY CONNECTION'}</span>
        </button>
      )}
    </div>
  );
};
