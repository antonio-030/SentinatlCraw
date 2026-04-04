import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import type { Severity } from '../types/api';

function cvssColor(score: number): string {
  if (score >= 9) return 'bg-severity-critical/10 text-severity-critical';
  if (score >= 7) return 'bg-severity-high/10 text-severity-high';
  if (score >= 4) return 'bg-severity-medium/10 text-severity-medium';
  return 'bg-severity-low/10 text-severity-low';
}

export function FindingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: finding, isLoading, isError } = useQuery({
    queryKey: ['finding', id],
    queryFn: () => api.findings.get(id!),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.findings.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings'] });
      navigate('/findings');
    },
  });

  function handleDelete() {
    if (window.confirm('Finding wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden.')) {
      deleteMutation.mutate();
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (isError || !finding) {
    return (
      <div className="space-y-4 max-w-4xl">
        <Link to="/findings" className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors">
          <ArrowLeft size={14} /> Back to Findings
        </Link>
        <p className="text-sm text-severity-critical">Failed to load finding details.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back link */}
      <Link to="/findings" className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors">
        <ArrowLeft size={14} /> Zurueck
      </Link>

      {/* Severity + Title header */}
      <div className="rounded-lg border border-border-subtle bg-bg-secondary p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="space-y-3">
            <SeverityBadge severity={finding.severity as Severity} />
            <h1 className="text-lg font-semibold text-text-primary">{finding.title}</h1>
          </div>
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-md border border-severity-critical/30 bg-severity-critical/10 px-3 py-1.5 text-xs font-medium text-severity-critical hover:bg-severity-critical/20 transition-colors self-start"
          >
            <Trash2 size={13} /> Loeschen
          </button>
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-text-secondary">
          {finding.cvss_score > 0 && (
            <span className={`inline-block rounded px-2.5 py-0.5 font-semibold tabular-nums ${cvssColor(finding.cvss_score)}`}>
              CVSS {finding.cvss_score.toFixed(1)}
            </span>
          )}
          {finding.cve_id && (
            <a
              href={`https://nvd.nist.gov/vuln/detail/${finding.cve_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-accent hover:underline"
            >
              {finding.cve_id}
            </a>
          )}
          <span className="font-mono">
            {finding.target_host}{finding.target_port ? `:${finding.target_port}` : ''}
          </span>
          {finding.service && <span>{finding.service}</span>}
        </div>
      </div>

      {/* Description */}
      {finding.description && (
        <div className="rounded-lg border border-border-subtle bg-bg-secondary p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-2">Description</h2>
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{finding.description}</p>
        </div>
      )}

      {/* Evidence */}
      {(finding as unknown as Record<string, unknown>).evidence && (
        <div className="rounded-lg border border-border-subtle bg-bg-secondary p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-2">Evidence</h2>
          <pre className="rounded-md bg-bg-primary border border-border-subtle p-4 text-xs text-text-secondary font-mono overflow-x-auto whitespace-pre-wrap">
            {String((finding as unknown as Record<string, unknown>).evidence)}
          </pre>
        </div>
      )}

      {/* Recommendation */}
      {finding.recommendation && (
        <div className="rounded-lg border border-accent/20 bg-accent/5 p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-2">Recommendation</h2>
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{finding.recommendation}</p>
        </div>
      )}
    </div>
  );
}
