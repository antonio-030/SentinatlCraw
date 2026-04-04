import { useQuery } from '@tanstack/react-query';
import { ScrollText } from 'lucide-react';
import { api } from '../services/api';
import type { AuditEntry } from '../types/api';

function formatTimestamp(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function actionColor(action: string) {
  if (action.includes('kill') || action.includes('delete')) return 'text-severity-critical';
  if (action.includes('create') || action.includes('start')) return 'text-status-success';
  if (action.includes('cancel') || action.includes('stop')) return 'text-severity-high';
  return 'text-text-primary';
}

export function AuditPage() {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: () => api.audit(100),
    refetchInterval: 15_000,
  });

  if (isLoading) return <div className="flex justify-center py-16"><div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-text-primary tracking-tight">Audit Log</h1>
        <p className="mt-1 text-sm text-text-secondary">Complete record of all system actions and events</p>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border-subtle bg-bg-secondary overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left">
                <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Timestamp</th>
                <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Action</th>
                <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Triggered By</th>
                <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Resource</th>
                <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {entries.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <ScrollText size={28} className="mx-auto mb-3 text-text-tertiary" strokeWidth={1.5} />
                    <p className="text-sm text-text-tertiary">No audit entries</p>
                    <p className="text-xs text-text-tertiary mt-1">System events will appear here</p>
                  </td>
                </tr>
              )}
              {entries.map((entry: AuditEntry) => (
                <tr key={entry.id} className="hover:bg-bg-tertiary/30 transition-colors">
                  <td className="px-5 py-3.5 text-xs text-text-tertiary tabular-nums font-mono whitespace-nowrap">
                    {formatTimestamp(entry.created_at)}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`text-xs font-semibold tracking-wide ${actionColor(entry.action)}`}>
                      {entry.action}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-text-secondary">
                    {entry.triggered_by}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-text-secondary font-mono">
                    {entry.resource_type
                      ? `${entry.resource_type}${entry.resource_id ? ` #${entry.resource_id.slice(0, 8)}` : ''}`
                      : '--'}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-text-tertiary max-w-xs truncate">
                    {Object.keys(entry.details).length > 0
                      ? JSON.stringify(entry.details)
                      : '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
