'use client';
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { MetricsResponse, ScenarioResponse } from '@/lib/types';

interface Props {
  metrics: MetricsResponse;
  scenario?: ScenarioResponse;
}

export default function CoverageChart({ metrics }: Props) {
  const rate = metrics.coverage_rate;
  const data = [
    { name: 'Filled', value: metrics.total_filled_positions },
    { name: 'Unfilled', value: metrics.unfilled_positions },
  ];

  return (
    <div>
      <p className="text-sm font-medium text-ink mb-1">
        Coverage: {(rate * 100).toFixed(1)}% ({metrics.total_filled_positions} / {metrics.total_required_positions} positions)
      </p>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 8 }}>
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={60} />
            <Tooltip />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              <Cell fill="#276749" />
              <Cell fill="#A33131" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
