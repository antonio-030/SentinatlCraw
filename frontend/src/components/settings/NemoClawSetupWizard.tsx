// ── NemoClaw Setup-Wizard ───────────────────────────────────────────
// Dreistufiger Wizard: Gateway-Status, Claude-Token, LLM-Provider.
// Wird oberhalb der NemoClaw-Einstellungs-Formulare angezeigt.

import { useState, useEffect, useCallback } from 'react';
import { CheckCircle2, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { showToast } from '../shared/NotificationToast';
import type { NemoClawSetupStatus } from '../../types/api';

// ── Hilfskomponente: Status-Icon je nach Zustand ────────────────────

function StepIcon({ ok, loading }: { ok: boolean; loading: boolean }) {
  if (loading) return <Loader2 size={20} className="animate-spin text-accent shrink-0" />;
  if (ok) return <CheckCircle2 size={20} className="text-status-success shrink-0" />;
  return <XCircle size={20} className="text-severity-critical shrink-0" />;
}

// ── Konstanten für Provider-Auswahl ─────────────────────────────────

const PROVIDER_OPTIONS = [
  { value: 'anthropic', label: 'Claude (Anthropic)' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'ollama', label: 'Ollama (Self-Hosted)' },
] as const;

// ── Wizard-Komponente ───────────────────────────────────────────────

export function NemoClawSetupWizard() {
  const [status, setStatus] = useState<NemoClawSetupStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Token-Formular
  const [tokenInput, setTokenInput] = useState('');
  const [tokenSaving, setTokenSaving] = useState(false);

  // Provider-Formular
  const [providerInput, setProviderInput] = useState('anthropic');
  const [modelInput, setModelInput] = useState('claude-sonnet-4-20250514');
  const [providerSaving, setProviderSaving] = useState(false);

  // Status vom Backend laden
  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.nemoclaw.setupStatus();
      setStatus(result);
    } catch (err) {
      showToast('error', 'Status-Abfrage fehlgeschlagen', (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Token speichern und validieren
  async function handleSaveToken() {
    if (!tokenInput.trim()) return;
    setTokenSaving(true);
    try {
      const result = await api.nemoclaw.saveToken(tokenInput.trim());
      if (result.valid) {
        showToast('success', 'Token gespeichert', result.message);
        setTokenInput('');
        await fetchStatus();
      } else {
        showToast('error', 'Token ungültig', result.message);
      }
    } catch (err) {
      showToast('error', 'Fehler beim Speichern', (err as Error).message);
    } finally {
      setTokenSaving(false);
    }
  }

  // Provider konfigurieren
  async function handleSetProvider() {
    if (!providerInput || !modelInput.trim()) return;
    setProviderSaving(true);
    try {
      const result = await api.nemoclaw.setProvider(providerInput, modelInput.trim());
      if (result.success) {
        showToast('success', 'Provider konfiguriert', result.message);
        await fetchStatus();
      } else {
        showToast('error', 'Konfiguration fehlgeschlagen', result.message);
      }
    } catch (err) {
      showToast('error', 'Fehler beim Konfigurieren', (err as Error).message);
    } finally {
      setProviderSaving(false);
    }
  }

  return (
    <div className="space-y-3 mb-6">
      <h3 className="text-sm font-semibold text-text-primary">Setup-Wizard</h3>

      {/* Schritt 1: Gateway-Status */}
      <div className="bg-bg-secondary border border-border-primary rounded-lg p-4">
        <div className="flex items-start gap-3">
          <StepIcon ok={!!status?.gateway_reachable} loading={loading} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-text-primary">1. Gateway-Status</p>
            {status && (
              <div className="mt-1.5 space-y-1">
                <p className="text-xs text-text-secondary">
                  Gateway:{' '}
                  <span className={`font-medium ${status.gateway_reachable ? 'text-status-success' : 'text-severity-critical'}`}>
                    {status.gateway_reachable ? 'Verbunden' : 'Nicht erreichbar'}
                  </span>
                  {status.gateway_name && (
                    <span className="text-text-tertiary ml-1.5 font-mono">({status.gateway_name})</span>
                  )}
                </p>
                {status.sandbox_name && (
                  <p className="text-xs text-text-secondary">
                    Sandbox: <span className="font-mono text-text-tertiary">{status.sandbox_name}</span>
                  </p>
                )}
                {!status.gateway_reachable && (
                  <p className="text-[11px] text-severity-medium mt-1">
                    Starte den NemoClaw Gateway mit: <code className="font-mono bg-bg-primary px-1.5 py-0.5 rounded text-text-primary">openshell gateway start</code>
                  </p>
                )}
              </div>
            )}
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-accent hover:text-accent-hover transition-colors disabled:opacity-50"
            >
              <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
              Status prüfen
            </button>
          </div>
        </div>
      </div>

      {/* Schritt 2: Claude Token */}
      <div className="bg-bg-secondary border border-border-primary rounded-lg p-4">
        <div className="flex items-start gap-3">
          <StepIcon ok={!!status?.token_configured} loading={loading} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-text-primary">2. Claude Token</p>
            {status?.token_configured ? (
              <p className="text-xs text-status-success mt-1.5 font-medium">Token konfiguriert</p>
            ) : (
              <div className="mt-1.5 space-y-2">
                <p className="text-[11px] text-text-tertiary">
                  Führe <code className="font-mono bg-bg-primary px-1.5 py-0.5 rounded text-text-primary">claude login</code> im Terminal aus und kopiere den angezeigten Token (sk-ant-...) hierher.
                </p>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    placeholder="sk-ant-..."
                    className="flex-1 rounded-md border border-border-default bg-bg-primary px-3 py-1.5 text-xs text-text-primary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                  <button
                    onClick={handleSaveToken}
                    disabled={tokenSaving || !tokenInput.trim()}
                    className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent/90 disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    {tokenSaving && <Loader2 size={12} className="animate-spin" />}
                    Token speichern & testen
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Schritt 3: LLM-Provider */}
      <div className="bg-bg-secondary border border-border-primary rounded-lg p-4">
        <div className="flex items-start gap-3">
          <StepIcon ok={!!status?.provider_configured} loading={loading} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-text-primary">3. LLM-Provider</p>
            {status?.provider_configured ? (
              <p className="text-xs text-status-success mt-1.5 font-medium">
                Provider: {status.provider_name} — {status.provider_model}
              </p>
            ) : (
              <div className="mt-1.5 space-y-2">
                <div className="flex gap-2">
                  <select
                    value={providerInput}
                    onChange={(e) => setProviderInput(e.target.value)}
                    className="rounded-md border border-border-default bg-bg-primary px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                    aria-label="LLM-Provider auswählen"
                  >
                    {PROVIDER_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={modelInput}
                    onChange={(e) => setModelInput(e.target.value)}
                    placeholder="Modell-Name"
                    className="flex-1 rounded-md border border-border-default bg-bg-primary px-3 py-1.5 text-xs text-text-primary font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>
                <button
                  onClick={handleSetProvider}
                  disabled={providerSaving || !modelInput.trim()}
                  className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent/90 disabled:opacity-50 transition-colors"
                >
                  {providerSaving && <Loader2 size={12} className="animate-spin" />}
                  Provider konfigurieren
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
