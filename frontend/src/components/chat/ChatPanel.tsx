// ── Agent Chat Panel — mit Resize und Live Activity Feed ────────────

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, X, Send, FileDown } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { AgentActivityFeed } from './AgentActivityFeed';
import { ToolDetailsToggle } from './ToolDetailsToggle';
import { useChatMessages } from '../../hooks/useChatMessages';
import type { LocalMessage } from '../../hooks/useChatMessages';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// ── Konstanten für Panel-Breite ─────────────────────────────────────
const CHAT_WIDTH_STORAGE_KEY = 'sc_chat_width';
const MIN_PANEL_WIDTH = 320;
const MAX_PANEL_WIDTH = 800;
const DEFAULT_PANEL_WIDTH = 380;

// ── Einzelne Nachricht rendern ──────────────────────────────────────

function MessageBubble({ msg, onNavigate }: {
  msg: LocalMessage;
  onNavigate: (scanId: string) => void;
}) {
  // Scan-Link als Spezialfall
  if (msg.content.startsWith('__SCAN_LINK__')) {
    const scanId = msg.content.replace('__SCAN_LINK__', '');
    return (
      <div className="w-full">
        <button
          onClick={() => onNavigate(scanId)}
          className="w-full rounded-lg border border-status-success/30 bg-status-success/10 p-3 text-left hover:bg-status-success/15 active:bg-status-success/20 transition-colors touch-manipulation"
        >
          <p className="text-xs font-semibold text-status-success mb-1">Scan gestartet</p>
          <p className="text-[11px] text-text-secondary">Tippe hier für Live-Fortschritt</p>
          <p className="text-[10px] font-mono text-text-tertiary mt-1">{scanId.slice(0, 8)}...</p>
        </button>
      </div>
    );
  }

  const bubbleStyle = msg.role === 'user'
    ? 'bg-accent/15 text-text-primary rounded-br-sm'
    : msg.role === 'system'
      ? 'bg-bg-tertiary text-text-tertiary text-center w-full rounded-lg'
      : 'bg-bg-secondary border border-border-subtle text-text-primary rounded-bl-sm';

  return (
    <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] rounded-xl px-3 py-2 ${bubbleStyle}`}>
        {msg.role === 'agent' && (
          <p className="text-[10px] font-semibold text-accent mb-1">Agent</p>
        )}
        {msg.role === 'agent' ? (
          <MarkdownRenderer content={msg.content} compact />
        ) : (
          <p className="text-[13px] whitespace-pre-wrap break-words">{msg.content}</p>
        )}
        {/* Tool-Details unter Agent-Nachrichten */}
        {msg.role === 'agent' && msg.metadata && msg.metadata !== '{}' && (
          <ToolDetailsToggle metadata={msg.metadata} />
        )}
        {/* Als Report speichern — bei langen Agent-Nachrichten */}
        {msg.role === 'agent' && msg.content.length > 400 && !msg.content.includes('automatisch gespeichert') && (
          <SaveAsReportButton content={msg.content} />
        )}
        <p className="text-[10px] text-text-tertiary mt-1">{msg.timestamp}</p>
      </div>
    </div>
  );
}

// ── "Als Report speichern" Button ───────────────────────────────────

function SaveAsReportButton({ content }: { content: string }) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const csrfMatch = document.cookie.match(/(?:^|;\s*)sc_csrf=([^;]*)/);
      const csrfToken = csrfMatch ? decodeURIComponent(csrfMatch[1]) : '';
      await fetch('/api/v1/chat/reports/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
        credentials: 'include',
        body: JSON.stringify({ content }),
      });
      setSaved(true);
    } catch {
      // Fehler still ignorieren
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <p className="text-[10px] text-status-success mt-1.5">
        ✓ Als Report gespeichert
      </p>
    );
  }

  return (
    <button
      onClick={handleSave}
      disabled={saving}
      className="flex items-center gap-1 mt-1.5 text-[10px] text-text-tertiary hover:text-accent transition-colors disabled:opacity-50"
    >
      <FileDown size={11} />
      {saving ? 'Speichern...' : 'Als Report speichern'}
    </button>
  );
}

// ── Hauptkomponente ─────────────────────────────────────────────────

export function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const {
    messages, sending, thinkingSeconds, agentSteps,
    handleSend: sendMessage, clearHistory,
  } = useChatMessages(isOpen);

  // ── Resizable Panel ───────────────────────────────────────────────
  const [panelWidth, setPanelWidth] = useState(() => {
    const saved = localStorage.getItem(CHAT_WIDTH_STORAGE_KEY);
    return saved ? parseInt(saved, 10) : DEFAULT_PANEL_WIDTH;
  });
  const resizingRef = useRef(false);
  const panelWidthRef = useRef(panelWidth);

  function startResize(mouseDownEvent: React.MouseEvent) {
    mouseDownEvent.preventDefault();
    resizingRef.current = true;

    function onMouseMove(moveEvent: MouseEvent) {
      if (!resizingRef.current) return;
      const newWidth = Math.max(
        MIN_PANEL_WIDTH,
        Math.min(MAX_PANEL_WIDTH, window.innerWidth - moveEvent.clientX),
      );
      setPanelWidth(newWidth);
      panelWidthRef.current = newWidth;
    }

    function onMouseUp() {
      resizingRef.current = false;
      localStorage.setItem(CHAT_WIDTH_STORAGE_KEY, String(panelWidthRef.current));
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  // Auto-Scroll bei neuen Nachrichten oder während Agent arbeitet
  useEffect(() => {
    const timer = setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
    return () => clearTimeout(timer);
  }, [messages.length, isOpen, sending]);

  function handleFormSubmit(formEvent: React.FormEvent) {
    formEvent.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput('');
    sendMessage(text);
  }

  function handleScanNavigate(scanId: string) {
    navigate(`/scans/${scanId}/live`);
    onClose();
  }

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={onClose} />

      <aside
        className="fixed right-0 top-0 bottom-0 z-50 w-full sm:w-[380px] lg:static lg:z-auto lg:shrink-0 bg-bg-primary border-l border-border-subtle"
        style={{ width: panelWidth }}
      >
        <div className="flex h-full">
          {/* Resize-Handle mit Drag-Bubble in der Mitte */}
          <div
            className="relative w-2 cursor-col-resize group shrink-0 hidden lg:flex items-center justify-center"
            onMouseDown={startResize}
            role="separator"
            aria-orientation="vertical"
            aria-label="Chat-Panel-Breite anpassen"
          >
            {/* Hover-Highlight Linie */}
            <div className="absolute inset-0 bg-transparent group-hover:bg-accent/20 group-active:bg-accent/40 transition-colors" />
            {/* Drag-Bubble in der Mitte */}
            <div className="relative z-10 w-4 h-8 rounded-full bg-bg-tertiary border border-border-default group-hover:bg-accent/30 group-hover:border-accent/50 group-active:bg-accent/50 transition-all flex items-center justify-center shadow-sm">
              <div className="flex flex-col gap-[3px]">
                <div className="w-0.5 h-0.5 rounded-full bg-text-tertiary group-hover:bg-accent" />
                <div className="w-0.5 h-0.5 rounded-full bg-text-tertiary group-hover:bg-accent" />
                <div className="w-0.5 h-0.5 rounded-full bg-text-tertiary group-hover:bg-accent" />
              </div>
            </div>
          </div>

          {/* Chat-Inhalt */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <div className="shrink-0 h-14 flex items-center justify-between px-4 border-b border-border-subtle bg-bg-secondary">
              <div className="flex items-center gap-2">
                <Bot size={18} className="text-accent" />
                <span className="text-sm font-semibold text-text-primary">Agent Chat</span>
                {messages.length > 0 && (
                  <span className="text-[10px] text-text-tertiary">({messages.length})</span>
                )}
              </div>
              <div className="flex items-center gap-1">
                {messages.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="px-2 py-1 rounded text-[10px] text-text-tertiary hover:text-text-secondary hover:bg-bg-tertiary"
                  >
                    Leeren
                  </button>
                )}
                <button onClick={onClose} className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-tertiary" aria-label="Schließen">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Nachrichten */}
            <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center px-4">
                  <Bot size={32} className="text-accent mb-3" />
                  <p className="text-sm text-text-primary mb-1">SentinelClaw Agent</p>
                  <p className="text-xs text-text-tertiary">Tippe eine Nachricht oder &quot;Scanne scanme.nmap.org&quot;</p>
                </div>
              )}

              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} onNavigate={handleScanNavigate} />
              ))}

              {sending && (
                <AgentActivityFeed steps={agentSteps} elapsedSeconds={thinkingSeconds} />
              )}

              <div ref={bottomRef} />
            </div>

            {/* Eingabe */}
            <form onSubmit={handleFormSubmit} className="flex items-center gap-2 p-3 border-t border-border-subtle bg-bg-secondary">
              <input
                type="text"
                value={input}
                onChange={formEvent => setInput(formEvent.target.value)}
                disabled={sending}
                placeholder="Nachricht..."
                autoComplete="off"
                className="flex-1 rounded-lg border border-border-subtle bg-bg-primary px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent/50 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="shrink-0 flex items-center justify-center h-12 w-12 rounded-lg bg-accent text-white active:bg-accent/70 disabled:opacity-30 touch-manipulation"
                aria-label="Senden"
              >
                <Send size={20} />
              </button>
            </form>
          </div>
        </div>
      </aside>
    </>
  );
}
