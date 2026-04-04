// ── SentinelClaw Login Page ──────────────────────────────────────────

import { useState, type FormEvent } from 'react';
import { Shield, Eye, EyeOff, Loader2, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

export function LoginPage() {
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.auth.login(email, password);
      login(res.token, res.user);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message.includes('401')
            ? 'Ungueltige Anmeldedaten. Bitte versuchen Sie es erneut.'
            : err.message
          : 'Ein unbekannter Fehler ist aufgetreten.',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-[100dvh] w-full items-center justify-center bg-bg-primary p-4">
      {/* Subtle background grid effect */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-20%,rgba(59,130,246,0.08),transparent)]" />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo block */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 ring-1 ring-accent/20">
            <Shield size={28} strokeWidth={1.8} className="text-accent" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold tracking-tight text-text-primary">
              SentinelClaw
            </h1>
            <p className="mt-1 text-xs font-medium tracking-wide text-text-tertiary uppercase">
              AI-gestuetzte Security Assessment Platform
            </p>
          </div>
        </div>

        {/* Card */}
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-border-subtle bg-bg-secondary p-6 sm:p-8 shadow-2xl shadow-black/30"
        >
          <h2 className="mb-6 text-sm font-semibold text-text-secondary tracking-wide uppercase">
            Anmeldung
          </h2>

          {/* Error banner */}
          {error && (
            <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-severity-critical/20 bg-severity-critical/5 px-3.5 py-3 text-xs text-severity-critical">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" strokeWidth={2} />
              <span>{error}</span>
            </div>
          )}

          {/* Email */}
          <label className="mb-4 block">
            <span className="mb-1.5 block text-[11px] font-medium text-text-tertiary uppercase tracking-wider">
              E-Mail
            </span>
            <input
              type="email"
              required
              autoFocus
              autoComplete="email"
              placeholder="admin@sentinelclaw.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border-default bg-bg-primary px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-tertiary/60 outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent/30"
            />
          </label>

          {/* Password */}
          <label className="mb-6 block">
            <span className="mb-1.5 block text-[11px] font-medium text-text-tertiary uppercase tracking-wider">
              Passwort
            </span>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                autoComplete="current-password"
                placeholder="Passwort eingeben"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-border-default bg-bg-primary px-3.5 py-2.5 pr-10 text-sm text-text-primary placeholder:text-text-tertiary/60 outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent/30"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-text-tertiary hover:text-text-secondary transition-colors"
                tabIndex={-1}
                aria-label={showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !email || !password}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Authentifizierung...
              </>
            ) : (
              'Anmelden'
            )}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-6 text-center text-[10px] text-text-tertiary/60 tracking-wide">
          SentinelClaw v0.1 &mdash; Autorisierter Zugang erforderlich
        </p>
      </div>
    </div>
  );
}
