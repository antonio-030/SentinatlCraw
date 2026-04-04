import { useState, useMemo } from 'react';
import { FileText, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useScans } from '../hooks/useApi';
import { api } from '../services/api';
import { formatDate } from '../utils/format';
import type { Scan } from '../types/api';

type ReportType = 'executive' | 'technical' | 'compliance';

interface ReportState {
  scanId: string;
  type: ReportType;
  content: string;
}

export function ReportsPage() {
  const { data: scans = [], isLoading } = useScans();
  const [openReport, setOpenReport] = useState<ReportState | null>(null);
  const [loadingReport, setLoadingReport] = useState<string | null>(null);

  const completedScans = useMemo(
    () =>
      (scans as Scan[])
        .filter((s) => s.status === 'completed')
        .sort((a, b) => new Date(b.completed_at!).getTime() - new Date(a.completed_at!).getTime()),
    [scans],
  );

  async function handleReport(scanId: string, type: ReportType) {
    const key = `${scanId}-${type}`;

    // Toggle off if the same report is already open
    if (openReport?.scanId === scanId && openReport?.type === type) {
      setOpenReport(null);
      return;
    }

    setLoadingReport(key);
    try {
      const content = await api.scans.report(scanId, type);
      setOpenReport({ scanId, type, content });
    } catch (err) {
      setOpenReport({
        scanId,
        type,
        content: `Error: ${err instanceof Error ? err.message : 'Failed to load report'}`,
      });
    } finally {
      setLoadingReport(null);
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-text-primary tracking-tight">Reports</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Generate and view reports for completed scans
        </p>
      </div>

      {/* Scan List */}
      <div className="space-y-3">
        {completedScans.length === 0 && (
          <div className="rounded-lg border border-border-subtle bg-bg-secondary px-5 py-12 text-center">
            <FileText size={28} className="mx-auto mb-3 text-text-tertiary" strokeWidth={1.5} />
            <p className="text-sm text-text-tertiary">No completed scans with findings</p>
            <p className="text-xs text-text-tertiary mt-1">Run a scan to generate reports</p>
          </div>
        )}

        {completedScans.map((scan) => {
          const isOpen = openReport?.scanId === scan.id;
          return (
            <div
              key={scan.id}
              className="rounded-lg border border-border-subtle bg-bg-secondary overflow-hidden"
            >
              {/* Scan Row */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 px-5 py-4">
                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono text-text-primary truncate">{scan.target}</p>
                  <p className="text-xs text-text-tertiary mt-0.5">
                    {formatDate(scan.completed_at)} &middot; {scan.tokens_used.toLocaleString()} tokens
                  </p>
                </div>

                {/* Report Buttons */}
                <div className="flex flex-col sm:flex-row gap-2">
                  {(['executive', 'technical', 'compliance'] as ReportType[]).map((type) => {
                    const key = `${scan.id}-${type}`;
                    const isActive = openReport?.scanId === scan.id && openReport?.type === type;
                    const labels: Record<ReportType, string> = {
                      executive: 'Executive',
                      technical: 'Technisch',
                      compliance: 'Compliance',
                    };
                    return (
                      <button
                        key={type}
                        onClick={() => handleReport(scan.id, type)}
                        disabled={loadingReport === key}
                        className={`flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                          isActive
                            ? 'bg-accent text-white'
                            : 'border border-border-default text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
                        } disabled:opacity-40 disabled:cursor-not-allowed`}
                      >
                        {loadingReport === key ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : isActive ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                        {labels[type]}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Report Content */}
              {isOpen && openReport && (
                <div className="border-t border-border-subtle bg-bg-primary">
                  <div className="px-5 py-3 flex items-center justify-between border-b border-border-subtle">
                    <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
                      {openReport.type} Report
                    </span>
                    <button
                      onClick={() => setOpenReport(null)}
                      className="text-xs text-text-tertiary hover:text-text-secondary transition-colors"
                    >
                      Close
                    </button>
                  </div>
                  <pre className="px-5 py-4 text-xs text-text-primary font-mono whitespace-pre-wrap break-words max-h-[60vh] overflow-y-auto leading-relaxed">
                    {openReport.content}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
