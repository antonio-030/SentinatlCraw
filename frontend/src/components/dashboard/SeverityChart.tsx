import type { Finding } from '../../types/api';

const barColors: Record<string, string> = {
  critical: 'bg-severity-critical',
  high: 'bg-severity-high',
  medium: 'bg-severity-medium',
  low: 'bg-severity-low',
  info: 'bg-severity-info',
};

const labels: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
};

interface SeverityChartProps {
  findings: Finding[];
}

export function SeverityChart({ findings }: SeverityChartProps) {
  const counts: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  for (const f of findings) {
    counts[f.severity] = (counts[f.severity] || 0) + 1;
  }

  const max = Math.max(...Object.values(counts), 1);

  return (
    <div className="space-y-2.5">
      {Object.entries(counts).map(([severity, count]) => (
        <div key={severity} className="flex items-center gap-3">
          <span className="text-xs text-text-secondary w-14 text-right tabular-nums">
            {labels[severity]}
          </span>
          <div className="flex-1 h-5 rounded-sm bg-bg-primary overflow-hidden">
            <div
              className={`h-full rounded-sm transition-all duration-500 ${barColors[severity]}`}
              style={{ width: `${(count / max) * 100}%`, minWidth: count > 0 ? '2px' : 0 }}
            />
          </div>
          <span className="text-xs font-medium text-text-primary w-8 tabular-nums">{count}</span>
        </div>
      ))}
    </div>
  );
}
