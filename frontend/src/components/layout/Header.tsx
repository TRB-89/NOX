import React, { useState, useEffect } from 'react';
import { Menu, Terminal, Radio } from 'lucide-react';
import { api } from '../../services/api';
import { HealthStatus } from '../../types';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenMobileNav: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onOpenMobileNav }) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await api.getHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) {
          setHealth({
            status: 'error',
            model_loaded: false,
            model_version: 'Offline',
            threshold: null,
            device: null,
          });
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

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

  const isConnected = health?.status === 'ready' && health.model_loaded;

  return (
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
        {/* Backend Connection Indicator */}
        <div className="flex items-center gap-2 border border-border px-2.5 py-1.5 bg-surface font-mono text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-success animate-pulse' : 'bg-critical'
            }`}
          />
          <span className="text-[11px] text-chrome font-semibold uppercase hidden sm:inline">
            {isConnected ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>

        {/* Real-time System Clock */}
        <div className="flex items-center gap-2 font-mono text-xs text-chrome border border-border px-3 py-1.5 bg-surface">
          <Terminal className="w-3.5 h-3.5 text-accent" />
          <span className="tracking-widest">{timeStr}</span>
        </div>
      </div>
    </header>
  );
};
