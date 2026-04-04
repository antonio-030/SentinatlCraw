import { useState } from 'react';
import { Shield, Zap } from 'lucide-react';
import { api } from '../../services/api';

interface TopBarProps {
  systemOnline: boolean;
}

export function TopBar({ systemOnline }: TopBarProps) {
  const [killing, setKilling] = useState(false);

  async function handleKill() {
    if (!confirm('EMERGENCY KILL SWITCH\n\nThis will terminate ALL running scans immediately.\n\nContinue?')) return;
    setKilling(true);
    try {
      await api.kill('Manual kill switch activated from UI');
    } catch {
      // swallow — kill is best-effort
    } finally {
      setKilling(false);
    }
  }

  return (
    <header className="h-14 shrink-0 border-b border-border-subtle bg-bg-secondary flex items-center justify-between px-5 gap-4">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/10 text-accent">
          <Shield size={18} strokeWidth={2} />
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-sm font-semibold tracking-wide text-text-primary">SentinelClaw</span>
          <span className="text-[10px] font-medium text-text-tertiary tracking-widest uppercase">v0.1</span>
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-4">
        {/* System status */}
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span
            className={`h-2 w-2 rounded-full ${
              systemOnline
                ? 'bg-status-success shadow-[0_0_6px_rgba(34,197,94,0.4)]'
                : 'bg-status-error shadow-[0_0_6px_rgba(239,68,68,0.4)]'
            }`}
          />
          {systemOnline ? 'Systems Nominal' : 'Offline'}
        </div>

        {/* Kill Switch */}
        <button
          onClick={handleKill}
          disabled={killing}
          className="flex items-center gap-2 rounded-md border border-severity-critical/30 bg-severity-critical/10 px-3 py-1.5 text-xs font-semibold text-severity-critical tracking-wide uppercase transition-all hover:bg-severity-critical/20 hover:border-severity-critical/50 hover:shadow-[0_0_12px_rgba(239,68,68,0.15)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Zap size={13} strokeWidth={2.5} />
          {killing ? 'Killing...' : 'Kill Switch'}
        </button>
      </div>
    </header>
  );
}
