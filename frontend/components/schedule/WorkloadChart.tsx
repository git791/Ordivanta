'use client';
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { MetricsResponse } from '@/lib/types';

export default function WorkloadChart({ metrics }: { metrics: MetricsResponse }) {
  const data = Object.entries(metrics.employee_hours || {})
    .map(([id, hours]) => ({ id, hours }))
    .sort((a, b) => b.hours - a.hours);

  if (data.length === 0) {
    return <p className="text-sm text-ink-muted py-4">No assignments to display.</p>;
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 8 }}>
          <XAxis type="number" tick={{ fontSize: 12 }} unit="h" />
          <YAxis type="category" dataKey="id" tick={{ fontSize: 11 }} width={80} />
          <Tooltip formatter={(v: unknown) => [`${Number(v).toFixed(1)}h`, 'Hours']} />
          <Bar dataKey="hours" fill="#245A81" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
