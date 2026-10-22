import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface SeverityChartProps {
  distribution?: {
    Normal: number;
    Low: number;
    Medium: number;
    High: number;
  };
  severityDistribution?: {
    Normal: number;
    Low: number;
    Medium: number;
    High: number;
  };
}

export const SeverityChart: React.FC<SeverityChartProps> = ({
  distribution,
  severityDistribution,
}) => {
  const dist = distribution || severityDistribution || {
    Normal: 0,
    Low: 0,
    Medium: 0,
    High: 0,
  };

  const total = Object.values(dist).reduce((a, b) => a + (Number(b) || 0), 0);

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-80 border-industrial bg-surface text-muted font-mono text-xs p-6 text-center">
        <span className="font-bold text-chrome uppercase">AWAITING THREAT SEVERITY DATA</span>
        <span className="text-[11px] text-muted mt-1 max-w-xs">
          Processed flow events will populate low, medium, and high alert tiers.
        </span>
      </div>
    );
  }

  const data = [
    { tier: 'Normal', count: dist.Normal || 0, color: '#79a995' },
    { tier: 'Low', count: dist.Low || 0, color: '#5a7f9e' },
    { tier: 'Medium', count: dist.Medium || 0, color: '#d97736' },
    { tier: 'High', count: dist.High || 0, color: '#db3346' },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      const pct = total > 0 ? ((item.count / total) * 100).toFixed(1) : '0';
      return (
        <div className="bg-background border border-border p-2.5 font-mono text-xs shadow-xl">
          <p className="text-chrome font-semibold">{item.tier} Threat</p>
          <p className="text-muted mt-1">
            Count: <span className="text-chrome">{item.count.toLocaleString()}</span> ({pct}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="border-industrial bg-surface p-5 h-80 flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h3 className="font-display text-xs uppercase tracking-widest text-chrome font-bold">
          ALERT SEVERITY DISTRIBUTION
        </h3>
        <span className="font-mono text-[10px] text-muted">
          TRIAGE TIERS
        </span>
      </div>

      <div className="flex-1 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <XAxis
              dataKey="tier"
              stroke="#888888"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              axisLine={{ stroke: '#292929' }}
            />
            <YAxis
              stroke="#888888"
              fontSize={10}
              fontFamily="monospace"
              tickLine={false}
              axisLine={{ stroke: '#292929' }}
              tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" radius={[0, 0, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`bar-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
