// ── Chat-Eingabefeld — simpel, funktioniert auf allen Geräten ──���─────

import { useState } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 p-3 border-t border-border-subtle bg-bg-secondary"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Nachricht eingeben..."
        autoComplete="off"
        className="flex-1 rounded-lg border border-border-subtle bg-bg-primary px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent/50 disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="shrink-0 flex items-center justify-center h-12 w-12 rounded-lg bg-accent text-white active:bg-accent/70 disabled:opacity-30 touch-manipulation"
        aria-label="Senden"
      >
        <Send size={20} />
      </button>
    </form>
  );
}
