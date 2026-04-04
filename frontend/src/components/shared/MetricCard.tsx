import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color?: string;       // tailwind text color class, e.g. "text-accent"
  iconColor?: string;   // tailwind color for icon background glow
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  color = 'text-text-primary',
  iconColor = 'text-accent',
}: MetricCardProps) {
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-secondary p-6 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-text-secondary tracking-wide">{label}</p>
        <p className={`mt-2 text-3xl font-semibold tabular-nums tracking-tight ${color}`}>
          {value}
        </p>
      </div>
      <div className={`shrink-0 rounded-lg bg-bg-tertiary p-2.5 ${iconColor}`}>
        <Icon size={20} strokeWidth={1.8} />
      </div>
    </div>
  );
}
