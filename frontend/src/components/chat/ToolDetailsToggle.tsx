// ── Aufklappbare Tool-Details unter Agent-Nachrichten ────────────────
//
// Zeigt eine kompakte Zusammenfassung der genutzten Tools als Button.
// Beim Klick werden die einzelnen Schritte mit Dauer und Status
// aufgeklappt — hilft dem Nutzer nachzuvollziehen, was der Agent tat.

import { useState, useMemo } from 'react';
import {
  ChevronRight, ChevronDown, Terminal, CheckCircle, XCircle,
} from 'lucide-react';

// ── Typen ───────────────────────────────────────────────────────────

interface ToolDetail {
  tool: string;
  command?: string;
  success?: boolean;
  duration_ms?: number;
  output_preview?: string;
}

interface ParsedMetadata {
  tools?: ToolDetail[];
  total_duration_ms?: number;
}

interface ToolDetailsToggleProps {
  metadata: string;
}

// ── Hilfsfunktion: Metadata sicher parsen ───────────────────────────

function parseMetadata(raw: string): ParsedMetadata | null {
  try {
    const parsed = JSON.parse(raw) as ParsedMetadata;
    if (!parsed.tools || parsed.tools.length === 0) return null;
    return parsed;
  } catch {
    return null;
  }
}

// ── Hauptkomponente ─────────────────────────────────────────────────

export function ToolDetailsToggle({ metadata }: ToolDetailsToggleProps) {
  const [expanded, setExpanded] = useState(false);

  const parsed = useMemo(() => parseMetadata(metadata), [metadata]);
  if (!parsed || !parsed.tools) return null;

  const toolCount = parsed.tools.length;
  const totalDuration = parsed.total_duration_ms
    ? `${(parsed.total_duration_ms / 1000).toFixed(1)}s`
    : null;

  return (
    <div className="mt-1.5">
      {/* Kompakter Toggle-Button */}
      <button
        onClick={() => setExpanded(prev => !prev)}
        className="flex items-center gap-1 text-[10px] text-text-tertiary hover:text-text-secondary transition-colors"
        aria-expanded={expanded}
        aria-label={`${toolCount} Tools ${expanded ? 'einklappen' : 'aufklappen'}`}
      >
        {expanded
          ? <ChevronDown size={12} />
          : <ChevronRight size={12} />
        }
        <Terminal size={10} />
        <span>
          {toolCount} {toolCount === 1 ? 'Tool' : 'Tools'}
          {totalDuration && <span className="ml-1 font-mono">{totalDuration}</span>}
        </span>
      </button>

      {/* Aufgeklappte Details */}
      {expanded && (
        <div className="mt-1.5 space-y-1 border-l border-border-subtle ml-1.5 pl-2.5">
          {parsed.tools.map((tool, index) => {
            const isSuccess = tool.success !== false;
            const durationLabel = tool.duration_ms
              ? `${(tool.duration_ms / 1000).toFixed(1)}s`
              : null;

            return (
              <div key={`${tool.tool}-${index}`} className="flex items-start gap-1.5">
                {isSuccess ? (
                  <CheckCircle size={11} className="text-status-success shrink-0 mt-0.5" />
                ) : (
                  <XCircle size={11} className="text-severity-critical shrink-0 mt-0.5" />
                )}
                <div className="min-w-0">
                  <span className="text-[10px] font-mono text-text-secondary truncate block">
                    {tool.tool}
                    {tool.command ? ` ${tool.command}` : ''}
                  </span>
                  {(durationLabel || tool.output_preview) && (
                    <span className="text-[10px] text-text-tertiary">
                      {durationLabel && <span className="font-mono">{durationLabel}</span>}
                      {durationLabel && tool.output_preview && ' — '}
                      {tool.output_preview}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
