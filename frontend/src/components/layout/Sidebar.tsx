import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ShieldAlert, 
  Activity, 
  BarChart3, 
  Clock, 
  Cpu, 
  Radio, 
  X 
} from 'lucide-react';
import { api } from '../../services/api';
import { HealthStatus } from '../../types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
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

  const navItems = [
    { num: '01', label: 'Overview', to: '/', icon: Activity },
    { num: '02', label: 'Neural Detection', to: '/detect', icon: ShieldAlert },
    { num: '03', label: 'Threat Analytics', to: '/analytics', icon: BarChart3 },
    { num: '04', label: 'Detection History', to: '/history', icon: Clock },
    { num: '05', label: 'System Information', to: '/system', icon: Cpu },
  ];

  const isConnected = health?.status === 'ready' && health.model_loaded;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-sm transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-surface border-r border-border flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div>
          {/* Brand Heading */}
          <div className="p-6 border-b border-border flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 bg-accent inline-block" />
                <h1 className="font-display text-2xl font-bold tracking-tight text-chrome">
                  NØX
                </h1>
              </div>
              <p className="font-mono text-[10px] tracking-widest text-muted mt-1 uppercase">
                NEURAL INTRUSION SYSTEM
              </p>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden text-muted hover:text-chrome p-1 border border-border"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-3 border transition-colors duration-200 group ${
                      isActive
                        ? 'border-accent bg-background text-chrome font-medium'
                        : 'border-transparent text-muted hover:text-chrome hover:border-border hover:bg-background/50'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 text-muted group-hover:text-chrome transition-colors" />
                    <span className="font-mono text-xs uppercase tracking-wider">
                      {item.label}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-muted opacity-60">
                    {item.num}
                  </span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* System & Model Telemetry Footer */}
        <div className="p-4 m-4 border border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-muted uppercase tracking-widest">
              BACKEND STATUS
            </span>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isConnected ? 'bg-success animate-pulse' : 'bg-critical'
                }`}
              />
              <span className="font-mono text-[10px] text-chrome uppercase">
                {isConnected ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
          </div>

          <div className="space-y-1 font-mono text-[11px]">
            <div className="flex justify-between text-muted">
              <span>MODEL:</span>
              <span className="text-chrome font-semibold truncate max-w-[120px]">
                {health?.model_version || 'Unavailable'}
              </span>
            </div>
            <div className="flex justify-between text-muted">
              <span>DEVICE:</span>
              <span className="text-chrome uppercase">
                {health?.device || 'CPU'}
              </span>
            </div>
            <div className="flex justify-between text-muted">
              <span>SYS VER:</span>
              <span className="text-chrome">v1.0.0</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
