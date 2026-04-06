// ── Live-Activity-Feed während der Agent-Arbeit ─────────────────────
//
// Zeigt dem Nutzer in Echtzeit, welche Tools der Agent gerade ausführt,
// welche Ergebnisse zurückkommen und wie lange er schon arbeitet.

import { useEffect, useRef } from 'react';
import {
  Terminal, CheckCircle, XCircle, Brain, Loader2,
} from 'lucide-react';

// ── Typen ───────────────────────────────────────────────────────────

export interface AgentStep {
  type: 'thinking' | 'tool_start' | 'tool_result';
  tool?: string;
  command?: string;
  message?: string;
  success?: boolean;
  output_preview?: string;
  duration_ms?: number;
  iteration?: number;
  total_tools?: number;
}

interface AgentActivityFeedProps {
  steps: AgentStep[];
  elapsedSeconds: number;
}

// ── Einzelner Schritt im Feed ───────────────────────────────────────

function StepRow({ step }: { step: AgentStep }) {
  if (step.type === 'thinking') {
    return (
      <div className="flex items-start gap-2 animate-fade-in">
        <Brain size={14} className="text-text-secondary shrink-0 mt-0.5 animate-pulse" />
        <span className="text-xs text-text-secondary">
          {step.message ?? 'Analysiert Ergebnisse...'}
        </span>
      </div>
    );
  }

  if (step.type === 'tool_start') {
    return (
      <div className="flex items-start gap-2 animate-fade-in">
        <Terminal size={14} className="text-accent shrink-0 mt-0.5" />
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-text-primary font-mono truncate">
            {step.tool}{step.command ? ` ${step.command}` : ''}
          </span>
          <Loader2 size={12} className="text-accent animate-spin shrink-0" />
        </div>
      </div>
    );
  }

  // tool_result
  const isSuccess = step.success !== false;
  const durationLabel = step.duration_ms
    ? `${(step.duration_ms / 1000).toFixed(1)}s`
    : null;

  return (
    <div className="flex items-start gap-2 animate-fade-in">
      {isSuccess ? (
        <CheckCircle size={14} className="text-status-success shrink-0 mt-0.5" />
      ) : (
        <XCircle size={14} className="text-severity-critical shrink-0 mt-0.5" />
      )}
      <div className="min-w-0">
        <span className={`text-xs ${isSuccess ? 'text-status-success' : 'text-severity-critical'}`}>
          {durationLabel && <span className="font-mono mr-1.5">{durationLabel}</span>}
          {step.output_preview ?? (isSuccess ? 'Abgeschlossen' : 'Fehlgeschlagen')}
        </span>
      </div>
    </div>
  );
}

// ── Hauptkomponente ─────────────────────────────────────────────────

export function AgentActivityFeed({ steps, elapsedSeconds }: AgentActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-Scroll bei neuen Steps
  useEffect(() => {
    const timer = setTimeout(() => {
      scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 50);
    return () => clearTimeout(timer);
  }, [steps.length]);

  return (
    <div className="flex justify-start">
      <div className="bg-bg-secondary border border-accent/20 rounded-xl rounded-bl-sm px-3 py-2.5 max-w-[90%] w-full">
        {/* Kopfzeile mit pulsierendem Punkt */}
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
          <span className="text-[11px] font-semibold text-accent">
            Agent arbeitet...
          </span>
          <span className="text-[10px] text-text-tertiary tabular-nums font-mono ml-auto">
            {elapsedSeconds}s
          </span>
        </div>

        {/* Schrittliste mit vertikaler Linie */}
        <div className="space-y-1.5 border-l border-border-subtle ml-1 pl-3 max-h-48 overflow-y-auto">
          {steps.map((step, index) => (
            <StepRow key={`${step.type}-${index}`} step={step} />
          ))}

          {/* Abbruch-Option nach 15 Sekunden */}
          <div ref={scrollRef} />
        </div>
      </div>
    </div>
  );
}
