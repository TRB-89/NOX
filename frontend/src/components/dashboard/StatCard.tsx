import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label?: string;
  title?: string;
  value: string | number;
  subtext?: string;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'accent' | 'critical' | 'success';
  tone?: 'default' | 'accent' | 'critical' | 'success' | string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  title,
  value,
  subtext,
  subtitle,
  icon: Icon,
  variant,
  tone,
}) => {
  const displayLabel = title || label || '';
  const displaySubtext = subtitle || subtext;
  const activeVariant = (tone || variant || 'default') as 'default' | 'accent' | 'critical' | 'success';

  const getVariantStyles = () => {
    switch (activeVariant) {
      case 'accent':
      case 'critical':
        return 'border-accent/40 hover:border-accent text-accent';
      case 'success':
        return 'border-success/40 hover:border-success text-success';
      default:
        return 'border-border hover:border-chrome text-chrome';
    }
  };

  return (
    <div
      className={`p-5 bg-surface border transition-colors duration-200 relative overflow-hidden group ${getVariantStyles()}`}
    >
      {/* Decorative Corner Accent */}
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-border group-hover:border-chrome transition-colors" />

      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-xs uppercase tracking-widest text-muted">
          {displayLabel}
        </span>
        <div className="p-1.5 border border-border bg-background text-muted group-hover:text-chrome transition-colors">
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="font-display text-3xl font-bold tracking-tight text-chrome">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>

      {displaySubtext && (
        <p className="font-mono text-xs text-muted mt-2 truncate">
          {displaySubtext}
        </p>
      )}
    </div>
  );
};
