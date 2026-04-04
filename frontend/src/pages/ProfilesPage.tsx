import { useNavigate } from 'react-router-dom';
import { useProfiles } from '../hooks/useApi';
import { Layers, Clock, Zap, Globe, Loader2 } from 'lucide-react';
import type { ScanProfile } from '../types/api';

const ESCALATION_LABELS: Record<number, string> = {
  0: 'Passiv',
  1: 'Aktiv',
  2: 'Vuln-Check',
  3: 'Exploit',
  4: 'Post-Exploit',
};

const ESCALATION_COLORS: Record<number, string> = {
  0: 'bg-status-success/15 text-status-success',
  1: 'bg-accent/15 text-accent',
  2: 'bg-severity-medium/15 text-severity-medium',
  3: 'bg-severity-high/15 text-severity-high',
  4: 'bg-severity-critical/15 text-severity-critical',
};

function EscalationBadge({ level }: { level: number }) {
  const label = ESCALATION_LABELS[level] ?? `Stufe ${level}`;
  const colorClass = ESCALATION_COLORS[level] ?? 'bg-bg-tertiary text-text-secondary';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${colorClass}`}
    >
      <Zap size={11} />
      {label} (Stufe {level})
    </span>
  );
}

function ProfileCard({ profile }: { profile: ScanProfile }) {
  const navigate = useNavigate();

  const handleScan = () => {
    navigate(`/scans/new?profile=${encodeURIComponent(profile.name)}`);
  };

  return (
    <div className="flex flex-col rounded-lg border border-border-subtle bg-bg-secondary p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <Layers size={18} strokeWidth={1.8} className="text-accent shrink-0 mt-0.5" />
          <h2 className="text-base font-semibold text-text-primary leading-tight">
            {profile.name}
          </h2>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-text-secondary leading-relaxed mb-4">
        {profile.description}
      </p>

      {/* Meta rows */}
      <div className="space-y-2.5 mb-5 flex-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-text-tertiary">Ports</span>
          <span className="text-xs text-text-primary font-mono text-right truncate max-w-[180px]">
            {profile.ports || '--'}
          </span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-text-tertiary">Eskalationsstufe</span>
          <EscalationBadge level={profile.max_escalation_level} />
        </div>

        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-text-tertiary">Geschaetzte Dauer</span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-primary">
            <Clock size={12} className="text-text-tertiary" />
            ~{profile.estimated_duration_minutes} Min.
          </span>
        </div>
      </div>

      {/* Action */}
      <button
        onClick={handleScan}
        className="w-full rounded-md bg-accent/15 text-accent text-sm font-medium py-2.5 hover:bg-accent/25 transition-colors"
      >
        Scan mit diesem Profil
      </button>
    </div>
  );
}

export function ProfilesPage() {
  const { data: profiles, isLoading, isError, error } = useProfiles();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 size={24} className="animate-spin text-text-tertiary" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="rounded-lg border border-severity-high/20 bg-severity-high/5 px-5 py-4">
          <p className="text-sm text-severity-high">
            Fehler beim Laden der Profile: {(error as Error)?.message ?? 'Unbekannter Fehler'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Globe size={22} strokeWidth={1.8} className="text-text-tertiary mt-0.5 shrink-0" />
        <div>
          <h1 className="text-xl font-semibold text-text-primary tracking-tight">
            Scan-Profile
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Vordefinierte Konfigurationen fuer verschiedene Scan-Szenarien.
            Waehle ein Profil, um einen neuen Scan zu starten.
          </p>
        </div>
      </div>

      {/* Profile Grid */}
      {profiles && profiles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <ProfileCard key={profile.name} profile={profile} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-border-subtle bg-bg-secondary px-5 py-10 text-center">
          <Layers size={32} className="mx-auto text-text-tertiary mb-3" />
          <p className="text-sm text-text-secondary">
            Keine Scan-Profile verfuegbar.
          </p>
        </div>
      )}
    </div>
  );
}
