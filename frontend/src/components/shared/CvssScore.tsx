import { clsx } from 'clsx';

interface CvssScoreProps {
  score: number;
  compact?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 9.0) return 'bg-severity-critical/15 text-severity-critical border-severity-critical/30';
  if (score >= 7.0) return 'bg-severity-high/15 text-severity-high border-severity-high/30';
  if (score >= 4.0) return 'bg-severity-medium/15 text-severity-medium border-severity-medium/30';
  if (score > 0) return 'bg-severity-low/15 text-severity-low border-severity-low/30';
  return 'bg-bg-tertiary text-text-tertiary border-border-subtle';
}

export function CvssScore({ score, compact = false }: CvssScoreProps) {
  if (score <= 0) return null;

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded border font-mono font-semibold tabular-nums',
        getScoreColor(score),
        compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs',
      )}
    >
      {score.toFixed(1)}
    </span>
  );
}
