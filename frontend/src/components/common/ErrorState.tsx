import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'SYSTEM TELEMETRY ERROR',
  message = 'Failed to connect to the NØX FastAPI backend. Verify server is running on 127.0.0.1:8000.',
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
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 flex items-center gap-2 px-4 py-2 border border-border hover:border-accent text-xs font-mono text-chrome uppercase tracking-wider transition-colors duration-200"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          RETRY CONNECTION
        </button>
      )}
    </div>
  );
};
