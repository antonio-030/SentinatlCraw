import type { Severity } from '../../types/api';

const config: Record<Severity, { dot: string; text: string; bg: string }> = {
  critical: {
    dot: 'bg-severity-critical',
    text: 'text-severity-critical',
    bg: 'bg-severity-critical/10',
  },
  high: {
    dot: 'bg-severity-high',
    text: 'text-severity-high',
    bg: 'bg-severity-high/10',
  },
  medium: {
    dot: 'bg-severity-medium',
    text: 'text-severity-medium',
    bg: 'bg-severity-medium/10',
  },
  low: {
    dot: 'bg-severity-low',
    text: 'text-severity-low',
    bg: 'bg-severity-low/10',
  },
  info: {
    dot: 'bg-severity-info',
    text: 'text-severity-info',
    bg: 'bg-severity-info/10',
  },
};

interface SeverityBadgeProps {
  severity: Severity;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const c = config[severity];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium tracking-wide uppercase ${c.bg} ${c.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {severity}
    </span>
  );
}
