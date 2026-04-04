import { useStatus } from '../hooks/useApi';
import { ShieldCheck, Info, FileText, Globe, Loader2 } from 'lucide-react';

export function WhitelistPage() {
  const { data: status, isLoading, isError, error } = useStatus();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 size={24} className="animate-spin text-text-tertiary" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="rounded-lg border border-severity-high/20 bg-severity-high/5 px-5 py-4">
          <p className="text-sm text-severity-high">
            Fehler beim Laden der Whitelist: {(error as Error)?.message ?? 'Unbekannter Fehler'}
          </p>
        </div>
      </div>
    );
  }

  // Extract allowed targets from system status — currently the API returns
  // system info but not an explicit whitelist field.  We display what we
  // have and inform the user that config happens externally.
  const systemInfo = status?.system;

  // Placeholder targets — in the future the backend will expose a
  // dedicated /api/v1/whitelist endpoint. For now we show an informational
  // view explaining how the whitelist works.
  const targets: string[] = [];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start gap-3">
        <ShieldCheck size={22} strokeWidth={1.8} className="text-text-tertiary mt-0.5 shrink-0" />
        <div>
          <h1 className="text-xl font-semibold text-text-primary tracking-tight">
            Scan-Whitelist
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Verwaltung der erlaubten Scan-Ziele. Nur Ziele in dieser Liste koennen gescannt werden.
          </p>
        </div>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 rounded-lg border border-accent/20 bg-accent/5 px-5 py-4">
        <Info size={16} className="text-accent shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-sm text-text-primary font-medium">
            Nur Ziele in dieser Liste koennen gescannt werden.
          </p>
          <p className="text-xs text-text-secondary leading-relaxed">
            Die Whitelist stellt sicher, dass ausschliesslich autorisierte Netzwerke und Hosts
            als Scan-Ziel verwendet werden koennen. Nicht-gelistete Ziele werden vom Scanner abgelehnt.
          </p>
        </div>
      </div>

      {/* Targets list */}
      <section className="rounded-lg border border-border-subtle bg-bg-secondary">
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border-subtle">
          <Globe size={16} strokeWidth={1.8} className="text-text-tertiary shrink-0" />
          <h2 className="text-sm font-semibold text-text-primary tracking-wide">
            Erlaubte Ziele
          </h2>
        </div>

        <div className="px-5 py-4">
          {targets.length > 0 ? (
            <ul className="space-y-2">
              {targets.map((target) => (
                <li
                  key={target}
                  className="flex items-center gap-3 rounded-md border border-border-subtle bg-bg-tertiary/40 px-4 py-3"
                >
                  <ShieldCheck size={14} className="text-status-success shrink-0" />
                  <span className="text-sm text-text-primary font-mono">{target}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-6">
              <ShieldCheck size={28} className="mx-auto text-text-tertiary mb-2" />
              <p className="text-sm text-text-secondary">
                Keine Whitelist-Eintraege ueber die API verfuegbar.
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                Konfiguration erfolgt ueber die .env Datei oder API (siehe unten).
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Configuration note */}
      <section className="rounded-lg border border-border-subtle bg-bg-secondary">
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border-subtle">
          <FileText size={16} strokeWidth={1.8} className="text-text-tertiary shrink-0" />
          <h2 className="text-sm font-semibold text-text-primary tracking-wide">
            Konfiguration
          </h2>
        </div>

        <div className="px-5 py-4 space-y-3">
          <p className="text-sm text-text-secondary leading-relaxed">
            Whitelist wird ueber die <code className="text-xs font-mono bg-bg-tertiary px-1.5 py-0.5 rounded text-text-primary">.env</code> Datei
            oder API konfiguriert.
          </p>
          <div className="rounded-md bg-bg-tertiary border border-border-subtle px-4 py-3">
            <p className="text-xs font-mono text-text-secondary leading-relaxed">
              # Beispiel .env Konfiguration<br />
              ALLOWED_TARGETS=10.0.0.0/8,192.168.0.0/16,172.16.0.0/12
            </p>
          </div>
          <p className="text-xs text-text-tertiary">
            Systeminformationen: Version {systemInfo?.version ?? '--'} &middot;
            Docker {systemInfo?.docker ?? '--'}
          </p>
        </div>
      </section>
    </div>
  );
}
