import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface TrafficChartProps {
  normalCount: number;
  attackCount?: number;
  maliciousCount?: number;
}

export const TrafficChart: React.FC<TrafficChartProps> = ({
  normalCount,
  attackCount,
  maliciousCount,
}) => {
  const attacks = maliciousCount !== undefined ? maliciousCount : (attackCount || 0);
  const total = normalCount + attacks;

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-80 border-industrial bg-surface text-muted font-mono text-xs p-6 text-center">
        <span className="font-bold text-chrome uppercase">AWAITING TRAFFIC TELEMETRY</span>
        <span className="text-[11px] text-muted mt-1 max-w-xs">
          Upload records to generate normal versus malicious traffic distribution.
        </span>
      </div>
    );
  }

  const data = [
    { name: 'Normal Traffic', value: normalCount, color: '#79a995' },
    { name: 'Potential Attacks', value: attacks, color: '#a62735' },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const pct = ((item.value / total) * 100).toFixed(1);
      return (
        <div className="bg-background border border-border p-2.5 font-mono text-xs shadow-xl">
          <p className="text-chrome font-semibold">{item.name}</p>
          <p className="text-muted mt-1">
            Count: <span className="text-chrome">{item.value.toLocaleString()}</span> ({pct}%)
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
          TRAFFIC CLASSIFICATION BREAKDOWN
        </h3>
        <span className="font-mono text-[10px] text-muted">
          TOTAL: {total.toLocaleString()} FLOWS
        </span>
      </div>

      <div className="flex-1 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
              stroke="#080808"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => (
                <span className="font-mono text-xs text-chrome ml-1">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
