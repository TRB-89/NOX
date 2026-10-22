import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'INITIALIZING SYSTEM TELEMETRY',
  subtext = 'Synchronizing with PyTorch inference engine...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border-industrial bg-surface my-6">
      <Loader2 className="w-8 h-8 text-chrome animate-spin mb-4" />
      <span className="font-mono text-sm tracking-wider text-chrome font-semibold uppercase">
        {message}
      </span>
      {subtext && (
        <span className="font-mono text-xs text-muted mt-2">
          {subtext}
        </span>
      )}
    </div>
  );
};
