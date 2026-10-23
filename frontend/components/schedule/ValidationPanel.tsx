import React from 'react';
import type { Violation } from '@/lib/types';
import { ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

export default function ValidationPanel({ violations }: { violations: Violation[] }) {
  if (!violations || violations.length === 0) {
    return (
      <div className="bg-success-soft border border-success rounded-lg p-4 flex items-center gap-2">
        <span className="text-success text-lg" aria-hidden="true">✓</span>
        <p className="text-sm font-medium text-success">All constraints satisfied — no violations found.</p>
      </div>
    );
  }

  const errors = violations.filter(v => v.severity === 'error');
  const warnings = violations.filter(v => v.severity === 'warning');

  return (
    <div className="space-y-2">
      {errors.map((v, i) => (
        <div key={`err-${i}`} className="bg-danger-soft border border-danger rounded-lg p-3 flex items-start gap-2">
          <ExclamationTriangleIcon className="w-4 h-4 text-danger shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <span className="text-xs font-mono text-danger font-semibold">{v.code}</span>
            <p className="text-sm text-danger">{v.message}</p>
          </div>
        </div>
      ))}
      {warnings.map((v, i) => (
        <div key={`warn-${i}`} className="bg-warning-soft border border-warning rounded-lg p-3 flex items-start gap-2">
          <InformationCircleIcon className="w-4 h-4 text-warning shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <span className="text-xs font-mono text-warning font-semibold">{v.code}</span>
            <p className="text-sm text-warning">{v.message}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
