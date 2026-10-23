import React, { useState, useEffect } from 'react';
import { Menu, Terminal, RefreshCw, AlertTriangle } from 'lucide-react';
import { useBackend } from '../../services/BackendContext';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenMobileNav: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onOpenMobileNav }) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const {
    health,
    isOnline,
    isChecking,
    isColdStarting,
    coldStartAttempt,
    checkHealth,
    wakeUpBackend,
  } = useBackend();

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleDateString('en-GB', {
          year: 'numeric',
          month: 'short',
          day: '2-digit',
        }) +
          ' ' +
          now.toLocaleTimeString('en-GB', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }) +
          ' UTC'
      );
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-30 w-full bg-background/90 backdrop-blur-md border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onOpenMobileNav}
            className="lg:hidden p-2 border border-border text-muted hover:text-chrome hover:border-chrome"
            aria-label="Open mobile navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-display text-lg font-bold tracking-tight text-chrome uppercase">
                {title}
              </h2>
              <span className="hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-mono border border-border text-muted uppercase">
                NØX-OPS
              </span>
            </div>
            {subtitle && (
              <p className="font-mono text-xs text-muted mt-0.5 hidden md:block">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          {/* Backend Connection Indicator & Trigger */}
          <button
            onClick={() => (isOnline ? checkHealth(true) : wakeUpBackend())}
            disabled={isChecking || isColdStarting}
            className="flex items-center gap-2 border border-border px-2.5 py-1.5 bg-surface font-mono text-xs hover:border-chrome transition-colors cursor-pointer disabled:opacity-50"
            title={
              isOnline
                ? 'Backend connected and operational (click to re-verify)'
                : isColdStarting
                ? `Waking up backend (attempt ${coldStartAttempt}/5)...`
                : 'Backend offline. Click to wake up or ping server.'
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isChecking || isColdStarting
                  ? 'bg-accent animate-ping'
                  : isOnline
                  ? 'bg-success animate-pulse'
                  : 'bg-critical'
              }`}
            />
            <span className="text-[11px] text-chrome font-semibold uppercase hidden sm:inline">
              {isColdStarting
                ? `WAKING UP (${coldStartAttempt}/5)`
                : isChecking
                ? 'PROBING...'
                : isOnline
                ? 'ONLINE'
                : 'OFFLINE'}
            </span>
          </button>

          {/* Real-time System Clock */}
          <div className="flex items-center gap-2 font-mono text-xs text-chrome border border-border px-3 py-1.5 bg-surface">
            <Terminal className="w-3.5 h-3.5 text-accent" />
            <span className="tracking-widest">{timeStr}</span>
          </div>
        </div>
      </header>

      {/* Backend Offline / Render Cold Start Telemetry Banner */}
      {health && !isOnline && (
        <div className="bg-critical/10 border-b border-critical/30 px-6 py-2.5 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-critical font-medium">
            <span className="w-2 h-2 rounded-full bg-critical animate-ping shrink-0" />
            <span>
              {isColdStarting ? (
                <>
                  [WAKING UP BACKEND] Neural engine is spinning up on Render Free Tier (attempt {coldStartAttempt}/5, ~60s boot time). Telemetry will auto-sync upon ready...
                </>
              ) : (
                <>
                  [BACKEND OFFLINE] Neural inference server unreachable. If hosted on Render Free Tier, instance sleeps after 15m idle.
                </>
              )}
            </span>
          </div>
          <button
            onClick={() => wakeUpBackend()}
            disabled={isChecking || isColdStarting}
            className="text-chrome hover:text-white uppercase font-bold tracking-wider text-[11px] underline flex items-center gap-1.5 shrink-0 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isChecking || isColdStarting ? 'animate-spin' : ''}`} />
            <span>
              {isColdStarting
                ? `SPINNING UP (${coldStartAttempt}/5)...`
                : isChecking
                ? 'PROBING...'
                : 'WAKE UP BACKEND'}
            </span>
          </button>
        </div>
      )}
    </>
  );
};
