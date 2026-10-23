import clsx from 'clsx';
import type { SolverStatus } from '@/lib/types';

const STATUS_CONFIG: Record<SolverStatus, { label: string; symbol: string; bg: string; text: string; border: string }> = {
  OPTIMAL: { label: 'Optimal solution found', symbol: '✓', bg: 'bg-success-soft', text: 'text-success', border: 'border-success' },
  FEASIBLE: { label: 'Feasible — not proven optimal', symbol: '≈', bg: 'bg-warning-soft', text: 'text-warning', border: 'border-warning' },
  INFEASIBLE: { label: 'No schedule possible', symbol: '✕', bg: 'bg-danger-soft', text: 'text-danger', border: 'border-danger' },
  NOT_SOLVED: { label: 'No usable solution', symbol: '⊘', bg: 'bg-surface-muted', text: 'text-ink-muted', border: 'border-border' },
  ERROR: { label: 'Solver error', symbol: '⚠', bg: 'bg-danger-soft', text: 'text-danger', border: 'border-danger' },
};

interface StatusBadgeProps {
  status: SolverStatus;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    symbol: '•',
    bg: 'bg-surface-muted',
    text: 'text-ink-muted',
    border: 'border-border',
  };
  return (
    <span
      role="status"
      aria-label={config.label}
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium border rounded',
        config.bg, config.text, config.border,
        size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'
      )}
    >
      <span aria-hidden="true">{config.symbol}</span>
      {config.label}
    </span>
  );
}
