import { clsx } from 'clsx';

const statusConfig: Record<string, { color: string; label: string }> = {
  completed: { color: 'bg-status-success', label: 'Abgeschlossen' },
  running: { color: 'bg-status-running animate-pulse', label: 'Läuft' },
  pending: { color: 'bg-text-tertiary', label: 'Wartend' },
  failed: { color: 'bg-status-error', label: 'Fehlgeschlagen' },
  cancelled: { color: 'bg-text-tertiary', label: 'Abgebrochen' },
  emergency_killed: { color: 'bg-severity-critical', label: 'Gestoppt' },
};

interface StatusBadgeProps {
  status: string;
  compact?: boolean;
}

export function StatusBadge({ status, compact = false }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { color: 'bg-text-tertiary', label: status };

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={clsx('h-2 w-2 rounded-full shrink-0', config.color)} />
      {!compact && (
        <span className="text-xs text-text-secondary capitalize">{config.label}</span>
      )}
    </span>
  );
}
