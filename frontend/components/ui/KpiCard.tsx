import React from 'react';

interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  note?: string;
  className?: string;
}

export default function KpiCard({ label, value, note, className }: KpiCardProps) {
  return (
    <div className={`bg-surface border border-border rounded-lg p-5 ${className ?? ''}`}>
      <p className="text-xs font-medium text-ink-muted uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-semibold text-ink mt-1 font-mono tabular-nums">{value}</p>
      {note && <p className="text-xs text-ink-muted mt-1">{note}</p>}
    </div>
  );
}
