import React from 'react';
import clsx from 'clsx';
import type { SolverStatus } from '@/lib/types';

const STATUS_CONFIG: Record<
  SolverStatus,
  { label: string; dot: string; bg: string; text: string; border: string }
> = {
  OPTIMAL: {
    label: 'Optimal Solution Found',
    dot: 'bg-emerald-500',
    bg: 'bg-emerald-50/80',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
  },
  FEASIBLE: {
    label: 'Feasible (Not Proven Optimal)',
    dot: 'bg-amber-500',
    bg: 'bg-amber-50/80',
    text: 'text-amber-700',
    border: 'border-amber-200',
  },
  INFEASIBLE: {
    label: 'No Feasible Schedule',
    dot: 'bg-rose-500',
    bg: 'bg-rose-50/80',
    text: 'text-rose-700',
    border: 'border-rose-200',
  },
  NOT_SOLVED: {
    label: 'No Usable Solution',
    dot: 'bg-slate-400',
    bg: 'bg-slate-100',
    text: 'text-slate-600',
    border: 'border-slate-200',
  },
  ERROR: {
    label: 'Solver Execution Error',
    dot: 'bg-rose-600',
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
  },
};

interface StatusBadgeProps {
  status: SolverStatus;
  size?: 'sm' | 'md';
  customLabel?: string;
  className?: string;
}

export default function StatusBadge({
  status,
  size = 'md',
  customLabel,
  className,
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    dot: 'bg-slate-400',
    bg: 'bg-slate-100',
    text: 'text-slate-600',
    border: 'border-slate-200',
  };

  return (
    <span
      role="status"
      aria-label={config.label}
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium border rounded-full shadow-2xs transition-colors',
        config.bg,
        config.text,
        config.border,
        size === 'sm' ? 'text-[11px] px-2.5 py-0.5' : 'text-xs px-3 py-1',
        className
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0', config.dot)} aria-hidden="true" />
      {customLabel || config.label}
    </span>
  );
}
