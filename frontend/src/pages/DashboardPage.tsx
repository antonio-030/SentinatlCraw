import { useQuery } from '@tanstack/react-query';
import { Radar, AlertTriangle, ShieldAlert, Activity } from 'lucide-react';
import { api } from '../services/api';
import { MetricCard } from '../components/shared/MetricCard';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import type { Scan, Finding } from '../types/api';

function statusDot(status: string) {
  switch (status) {
    case 'completed': return 'bg-status-success';
    case 'running':   return 'bg-status-running animate-pulse';
    case 'failed':
    case 'killed':    return 'bg-status-error';
    default:          return 'bg-text-tertiary';
  }
}

function formatDate(iso: string | null) {
  if (!iso) return '--';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export function DashboardPage() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.status,
    refetchInterval: 10_000,
  });

  const { data: scans = [] } = useQuery({
    queryKey: ['scans'],
    queryFn: api.scans.list,
    refetchInterval: 15_000,
  });

  const { data: findings = [] } = useQuery({
    queryKey: ['findings'],
    queryFn: () => api.findings.list(),
    refetchInterval: 15_000,
  });

  const runningScans = status?.scans.running ?? 0;
  const criticalFindings = findings.filter((f: Finding) => f.severity === 'critical').length;
  const systemOnline = !!status;

  const recentScans = [...scans].sort(
    (a: Scan, b: Scan) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  ).slice(0, 5);

  const recentFindings = [...findings].sort(
    (a: Finding, b: Finding) => {
      const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      return (order[a.severity] ?? 5) - (order[b.severity] ?? 5);
    },
  ).slice(0, 5);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-text-primary tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-text-secondary">System overview and recent activity</p>
      </div>

      {/* Metric cards — 2 Spalten auf Mobile, 4 auf Desktop */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <MetricCard
          label="Running Scans"
          value={runningScans}
          icon={Radar}
          color="text-accent"
          iconColor="text-accent"
        />
        <MetricCard
          label="Total Findings"
          value={findings.length}
          icon={AlertTriangle}
          color="text-severity-medium"
          iconColor="text-severity-medium"
        />
        <MetricCard
          label="Critical Findings"
          value={criticalFindings}
          icon={ShieldAlert}
          color="text-severity-critical"
          iconColor="text-severity-critical"
        />
        <MetricCard
          label="System Status"
          value={systemOnline ? 'Online' : 'Offline'}
          icon={Activity}
          color={systemOnline ? 'text-status-success' : 'text-status-error'}
          iconColor={systemOnline ? 'text-status-success' : 'text-status-error'}
        />
      </div>

      {/* Tables row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Scans */}
        <section className="rounded-lg border border-border-subtle bg-bg-secondary">
          <div className="px-5 py-4 border-b border-border-subtle">
            <h2 className="text-sm font-semibold text-text-primary tracking-wide">Recent Scans</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle text-left">
                  <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Target</th>
                  <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Type</th>
                  <th className="px-5 py-3 text-xs font-medium text-text-tertiary uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {recentScans.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-sm text-text-tertiary">
                      No scans yet
                    </td>
                  </tr>
                )}
                {recentScans.map((scan: Scan) => (
                  <tr key={scan.id} className="hover:bg-bg-tertiary/30 transition-colors">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${statusDot(scan.status)}`} />
                        <span className="text-text-secondary capitalize text-xs">{scan.status}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-text-primary">{scan.target}</td>
                    <td className="px-5 py-3 text-xs text-text-secondary">{scan.scan_type}</td>
                    <td className="px-5 py-3 text-xs text-text-tertiary tabular-nums">{formatDate(scan.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Recent Findings */}
        <section className="rounded-lg border border-border-subtle bg-bg-secondary">
          <div className="px-5 py-4 border-b border-border-subtle">
            <h2 className="text-sm font-semibold text-text-primary tracking-wide">Recent Findings</h2>
          </div>
          <div className="divide-y divide-border-subtle">
            {recentFindings.length === 0 && (
              <div className="px-5 py-8 text-center text-sm text-text-tertiary">
                No findings yet
              </div>
            )}
            {recentFindings.map((finding: Finding) => (
              <div key={finding.id} className="flex items-center gap-4 px-5 py-3 hover:bg-bg-tertiary/30 transition-colors">
                <SeverityBadge severity={finding.severity} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-text-primary truncate">{finding.title}</p>
                  <p className="text-xs text-text-tertiary font-mono mt-0.5">
                    {finding.target_host}
                    {finding.target_port ? `:${finding.target_port}` : ''}
                  </p>
                </div>
                {finding.cvss_score > 0 && (
                  <span className="text-xs font-medium text-text-secondary tabular-nums">
                    CVSS {finding.cvss_score.toFixed(1)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
