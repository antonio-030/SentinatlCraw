import { useState, useMemo } from 'react';
import { Download, Loader2, CheckCircle } from 'lucide-react';
import { useScans } from '../hooks/useApi';
import { api } from '../services/api';
import { formatDate } from '../utils/format';
import type { Scan } from '../types/api';

type ExportFormat = 'csv' | 'jsonl' | 'sarif';

export function ExportPage() {
  const { data: scans = [], isLoading } = useScans();
  const [selectedScanId, setSelectedScanId] = useState('');
  const [exporting, setExporting] = useState(false);
  const [lastExport, setLastExport] = useState<{ format: string; timestamp: Date } | null>(null);

  const completedScans = useMemo(
    () =>
      (scans as Scan[])
        .filter((s) => s.status === 'completed')
        .sort((a, b) => new Date(b.completed_at!).getTime() - new Date(a.completed_at!).getTime()),
    [scans],
  );

  const selectedScan = completedScans.find((s) => s.id === selectedScanId);

  async function handleExport(format: ExportFormat) {
    if (!selectedScanId) return;

    setExporting(true);
    try {
      const blob = await api.scans.export(selectedScanId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan-${selectedScanId.slice(0, 8)}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setLastExport({ format: format.toUpperCase(), timestamp: new Date() });
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(false);
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
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-text-primary tracking-tight">Export</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Export scan results in various formats
        </p>
      </div>

      {/* Scan Selector */}
      <div className="rounded-lg border border-border-subtle bg-bg-secondary p-5 space-y-5">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            Select Scan
          </label>
          <select
            value={selectedScanId}
            onChange={(e) => setSelectedScanId(e.target.value)}
            className="w-full rounded-md border border-border-default bg-bg-primary px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30"
          >
            <option value="">-- Select a completed scan --</option>
            {completedScans.map((scan) => (
              <option key={scan.id} value={scan.id}>
                {scan.target} &mdash; {formatDate(scan.completed_at)}
              </option>
            ))}
          </select>
          {selectedScan && (
            <p className="mt-1.5 text-xs text-text-tertiary">
              ID: {selectedScan.id.slice(0, 8)}&hellip; &middot; Type: {selectedScan.scan_type} &middot;{' '}
              {selectedScan.tokens_used.toLocaleString()} tokens
            </p>
          )}
        </div>

        {/* Format Buttons */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-2">Format</label>
          <div className="flex flex-wrap gap-2">
            {(['csv', 'jsonl', 'sarif'] as ExportFormat[]).map((format) => (
              <button
                key={format}
                onClick={() => handleExport(format)}
                disabled={!selectedScanId || exporting}
                className="flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:text-text-primary hover:bg-bg-tertiary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {exporting ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Download size={14} />
                )}
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Last Export Info */}
        {lastExport && (
          <div className="flex items-center gap-2 text-xs text-status-success">
            <CheckCircle size={14} />
            <span>
              Last export: {lastExport.format} at{' '}
              {lastExport.timestamp.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </span>
          </div>
        )}
      </div>

      {/* Empty state if no scans */}
      {completedScans.length === 0 && (
        <div className="rounded-lg border border-border-subtle bg-bg-secondary px-5 py-12 text-center">
          <Download size={28} className="mx-auto mb-3 text-text-tertiary" strokeWidth={1.5} />
          <p className="text-sm text-text-tertiary">No completed scans available</p>
          <p className="text-xs text-text-tertiary mt-1">Complete a scan to enable exports</p>
        </div>
      )}
    </div>
  );
}
