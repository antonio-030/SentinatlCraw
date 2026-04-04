import { useHealth } from '../../hooks/useApi';
import { CheckCircle, XCircle } from 'lucide-react';

function HealthRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-text-secondary">{label}</span>
      <span className="flex items-center gap-1.5">
        {ok ? (
          <CheckCircle size={13} className="text-status-success" />
        ) : (
          <XCircle size={13} className="text-status-error" />
        )}
        <span className={`text-xs font-medium ${ok ? 'text-status-success' : 'text-status-error'}`}>
          {ok ? 'OK' : 'Fehler'}
        </span>
      </span>
    </div>
  );
}

export function SystemHealth() {
  const { data: health } = useHealth();

  if (!health) return null;

  return (
    <div className="space-y-1 divide-y divide-border-subtle">
      <HealthRow label="API-Server" ok={health.status === 'ok'} />
      <HealthRow label="Datenbank" ok={health.db_connected} />
      <HealthRow label="Sandbox" ok={health.sandbox_running} />
      <HealthRow label="LLM-Provider" ok={health.status === 'ok'} />
      <div className="flex items-center justify-between py-1.5">
        <span className="text-xs text-text-secondary">Version</span>
        <span className="text-xs font-mono text-text-tertiary">{health.version}</span>
      </div>
      <div className="flex items-center justify-between py-1.5">
        <span className="text-xs text-text-secondary">Provider</span>
        <span className="text-xs font-mono text-text-tertiary">{health.provider}</span>
      </div>
    </div>
  );
}
