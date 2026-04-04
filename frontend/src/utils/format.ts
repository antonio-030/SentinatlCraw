export function formatDate(iso: string | null): string {
  if (!iso) return '--';
  return new Date(iso).toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function formatDateShort(iso: string | null): string {
  if (!iso) return '--';
  return new Date(iso).toLocaleString('de-DE', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export const SEVERITY_ORDER: Record<string, number> = {
  critical: 0, high: 1, medium: 2, low: 3, info: 4,
};

export function compareSeverity(a: string, b: string): number {
  return (SEVERITY_ORDER[a] ?? 5) - (SEVERITY_ORDER[b] ?? 5);
}
