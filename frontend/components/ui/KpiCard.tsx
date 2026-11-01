import React from 'react';

interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  note?: string;
  badge?: {
    text: string;
    variant?: 'success' | 'warning' | 'danger' | 'purple' | 'neutral';
  };
  icon?: React.ReactNode;
  className?: string;
}

const BADGE_STYLES = {
  success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  danger: 'bg-rose-50 text-rose-700 border-rose-200',
  purple: 'bg-purple-50 text-purple-700 border-purple-200',
  neutral: 'bg-slate-100 text-slate-700 border-slate-200',
};

export default function KpiCard({
  label,
  value,
  note,
  badge,
  icon,
  className,
}: KpiCardProps) {
  const badgeStyle = badge ? BADGE_STYLES[badge.variant || 'purple'] : '';

  return (
    <div
      className={`bg-surface border border-border/80 rounded-2xl p-5 shadow-xs hover:shadow-sm transition-all duration-150 flex flex-col justify-between ${
        className ?? ''
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-ink-muted tracking-wide">
          {label}
        </span>
        {icon && <div className="text-ink-muted/80">{icon}</div>}
      </div>

      <div className="flex items-baseline gap-2.5">
        <span className="text-2xl font-bold text-ink tracking-tight font-mono tabular-nums">
          {value}
        </span>
        {badge && (
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${badgeStyle}`}
          >
            {badge.text}
          </span>
        )}
      </div>

      {note && (
        <p className="text-xs text-ink-muted mt-2 font-normal line-clamp-1">
          {note}
        </p>
      )}
    </div>
  );
}
