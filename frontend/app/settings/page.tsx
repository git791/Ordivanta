'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { HealthResponse } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ServerIcon,
  CpuChipIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

const KNOWN_LIMITATIONS = [
  'Single-user prototype persistence: Runs and scenarios use SQLite by default; multi-user PostgreSQL requires manual migration.',
  'Rigid shift windows: Shifts use fixed start/end durations without intermediate rest-break micro-modelling.',
  'Cost minimisation requires complete wage/cost attributes configured in the active scenario.',
  'Fairness objective (balanced workload variance) is planned and not yet active in current solver formulations.',
  'External solver requirement: MILP optimization relies on HiGHS or CBC installed on the backend host.',
  'Greedy baseline is a heuristic and cannot prove mathematical optimality; use it strictly as a speed benchmark.',
  'Hard constraint adherence: The solver will never silently relax constraints or return partial schedules as optimal.',
];

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [lastChecked, setLastChecked] = useState<string>('');

  const checkHealth = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await api.health();
      setHealth(data);
    } catch (err: unknown) {
      console.error('Health check failed:', err);
      setHealth({
        status: 'offline',
        solver_available: false,
        solver_name: 'Unavailable',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLastChecked(new Date().toLocaleTimeString());
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const isOnline = health?.status === 'ok' || health?.status === 'healthy' || health?.status === 'online';
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  if (loading) {
    return <LoadingSpinner label="Checking system and solver health…" />;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Settings & System Diagnostics"
        description="Backend API connectivity, optimization solver telemetry, and environment configuration."
        action={
          <button
            type="button"
            onClick={checkHealth}
            disabled={refreshing}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-all disabled:opacity-50 shadow-2xs"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
            {refreshing ? 'Checking…' : 'Refresh Diagnostics'}
          </button>
        }
      />

      {/* Backend & Solver Diagnostics Card */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-5 shadow-sm">
        <div className="flex items-center justify-between border-b border-border/70 pb-4">
          <div className="flex items-center gap-2.5">
            <ServerIcon className="w-5 h-5 text-purple-600" aria-hidden="true" />
            <h2 className="text-base font-bold text-slate-900">Service Diagnostics</h2>
          </div>
          {lastChecked && (
            <span className="text-xs text-slate-500 font-mono">Last checked: {lastChecked}</span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Status */}
          <div className="p-4 bg-slate-50/70 rounded-2xl border border-slate-200/80 space-y-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Backend Status</span>
            <div className="flex items-center gap-2 pt-1">
              {isOnline ? (
                <>
                  <CheckCircleIcon className="w-5 h-5 text-emerald-600" aria-hidden="true" />
                  <span className="font-semibold text-emerald-800 text-sm">Online (Responding)</span>
                </>
              ) : (
                <>
                  <XCircleIcon className="w-5 h-5 text-red-600" aria-hidden="true" />
                  <span className="font-semibold text-red-800 text-sm">Offline (Unreachable)</span>
                </>
              )}
            </div>
          </div>

          {/* Solver Availability */}
          <div className="p-4 bg-slate-50/70 rounded-2xl border border-slate-200/80 space-y-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">MILP Solver Engine</span>
            <div className="flex items-center gap-2 pt-1">
              <CpuChipIcon className="w-5 h-5 text-purple-600" aria-hidden="true" />
              <span className="font-semibold text-slate-900 text-sm">
                {health?.solver_available ? 'Available' : 'Unavailable'}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              {health?.solver_available ? 'Ready for optimization runs' : 'Check backend solver setup'}
            </p>
          </div>

          {/* Solver Name */}
          <div className="p-4 bg-slate-50/70 rounded-2xl border border-slate-200/80 space-y-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Solver Backend</span>
            <div className="pt-1">
              <span className="font-mono font-bold text-slate-900 text-sm">
                {health?.solver_name || 'N/A'}
              </span>
            </div>
            <p className="text-xs text-slate-500">Configured via PuLP</p>
          </div>
        </div>
      </div>

      {/* Environment Section */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-4 shadow-sm">
        <h2 className="text-base font-bold text-slate-900">Environment Configuration</h2>
        <div className="border border-border/70 rounded-2xl overflow-hidden">
          <table className="w-full text-xs">
            <tbody className="divide-y divide-border/60">
              <tr>
                <td className="px-4 py-3 bg-slate-50/80 font-mono text-slate-500 w-1/3">
                  NEXT_PUBLIC_API_BASE_URL
                </td>
                <td className="px-4 py-3 font-mono text-slate-900 font-semibold">{apiBase}</td>
              </tr>
              <tr>
                <td className="px-4 py-3 bg-slate-50/80 font-mono text-slate-500">
                  Client Framework
                </td>
                <td className="px-4 py-3 text-slate-800 font-medium">Next.js (App Router) + React 19 + TypeScript</td>
              </tr>
              <tr>
                <td className="px-4 py-3 bg-slate-50/80 font-mono text-slate-500">
                  Design System
                </td>
                <td className="px-4 py-3 text-slate-800 font-medium">Truck&Co Executive B2B Theme (Tailwind CSS tokens)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Known Limitations */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-3 shadow-sm">
        <div className="flex items-center gap-2 text-slate-900">
          <InformationCircleIcon className="w-5 h-5 text-purple-600" aria-hidden="true" />
          <h2 className="text-base font-bold">System & Operational Scope</h2>
        </div>
        <p className="text-xs text-slate-500">
          Active architectural boundaries and constraints for this release:
        </p>
        <ul className="space-y-2 text-xs text-slate-700 list-disc list-inside">
          {KNOWN_LIMITATIONS.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
