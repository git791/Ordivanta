'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { SolveResponse, ScenarioResponse } from '@/lib/types';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import WorkforceTimelinePlanner from '@/components/schedule/WorkforceTimelinePlanner';
import RosterTable from '@/components/schedule/RosterTable';
import CoverageChart from '@/components/schedule/CoverageChart';
import WorkloadChart from '@/components/schedule/WorkloadChart';
import ValidationPanel from '@/components/schedule/ValidationPanel';
import {
  InformationCircleIcon,
  ArrowDownTrayIcon,
  TableCellsIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

export default function ScheduleRunDetailsPage() {
  const params = useParams();
  const runId = params?.runId as string;

  const [run, setRun] = useState<SolveResponse | null>(null);
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [displayMode, setDisplayMode] = useState<'timeline' | 'table'>('timeline');

  // Filters
  const [filterShift, setFilterShift] = useState<string>('');
  const [filterUnit, setFilterUnit] = useState<string>('');
  const [filterEmployee, setFilterEmployee] = useState<string>('');

  const fetchData = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const runData = await api.getRun(runId);
      setRun(runData);

      if (runData && runData.scenario_id) {
        try {
          const scenarioData = await api.getScenario(runData.scenario_id);
          setScenario(scenarioData);
        } catch (scErr) {
          console.warn('Could not fetch scenario for run:', scErr);
        }
      }
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : `Failed to load schedule run "${runId}".`);
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <LoadingSpinner label={`Loading schedule run ${runId}…`} />;
  }

  if (error || !run) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Link href="/schedule" className="hover:underline">← Schedule Builder</Link>
          <span>/</span>
          <span className="font-mono">{runId}</span>
        </div>
        <ErrorBanner title="Schedule Run Not Found" message={error ?? 'Run details could not be retrieved.'} />
        <Link
          href="/dashboard"
          className="inline-block px-5 py-2.5 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors shadow-2xs"
        >
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const isExportable = run.status === 'OPTIMAL' || run.status === 'FEASIBLE';

  const handleExportCsv = () => {
    if (!isExportable) return;
    window.open(api.exportCsvUrl(runId), '_blank');
  };

  return (
    <div className="space-y-8">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-500">
          <Link href="/dashboard" className="hover:underline">Dashboard</Link>
          <span>/</span>
          <Link href="/schedule" className="hover:underline">Schedule</Link>
          <span>/</span>
          <span className="font-mono text-slate-900 font-bold">{run.run_id}</span>
        </div>
        <Link
          href="/schedule"
          className="px-3.5 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 rounded-full hover:bg-purple-100 text-xs font-semibold transition-all shadow-2xs"
        >
          + New Schedule Run
        </Link>
      </div>

      {/* Header Banner (Truck&Co Style Card) */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-bold font-mono text-slate-900 tracking-tight">{run.run_id}</h1>
            <StatusBadge status={run.status} />
            <span className="font-mono text-xs uppercase px-3 py-1 bg-slate-100 rounded-full border border-slate-200/90 text-slate-800 font-bold">
              {run.algorithm}
            </span>
          </div>
          <div className="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span>
              Scenario:{' '}
              <strong className="text-slate-900 font-semibold">
                {scenario?.name ?? run.scenario_id}
              </strong>
            </span>
            <span>•</span>
            <span>
              Solver Time:{' '}
              <strong className="text-slate-900 font-mono font-semibold">{run.runtime_seconds.toFixed(3)}s</strong>
            </span>
            <span>•</span>
            <span>
              Executed:{' '}
              <strong className="text-slate-900 font-medium">{new Date(run.created_at).toLocaleString()}</strong>
            </span>
            {run.objective_value !== null && (
              <>
                <span>•</span>
                <span>
                  Objective:{' '}
                  <strong className="text-purple-700 font-mono font-bold">{run.objective_value.toFixed(2)}</strong>
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={!isExportable}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold transition-all shadow-2xs ${
              isExportable
                ? 'bg-slate-900 text-white hover:bg-slate-800 cursor-pointer'
                : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
            }`}
            title={isExportable ? 'Export schedule assignments to CSV' : 'Export only available for OPTIMAL or FEASIBLE status'}
          >
            <ArrowDownTrayIcon className="w-4 h-4 shrink-0" aria-hidden="true" />
            Export CSV Roster
          </button>
        </div>
      </div>

      {/* Warnings List (if any) */}
      {run.warnings && run.warnings.length > 0 && (
        <div className="bg-purple-50/70 border border-purple-200/80 rounded-2xl p-4 flex items-start gap-3 shadow-2xs">
          <InformationCircleIcon className="w-5 h-5 text-purple-700 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-xs font-bold text-purple-900">Schedule Formulation Warnings</p>
            <ul className="mt-1 list-disc list-inside text-xs text-slate-700 space-y-0.5">
              {run.warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Overview Analytics Row: Coverage + Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Coverage Section */}
        <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Coverage & Headcount Rate</h2>
            <span className="font-mono font-bold text-lg text-purple-700">
              {(run.metrics.coverage_rate * 100).toFixed(1)}%
            </span>
          </div>

          <CoverageChart metrics={run.metrics} scenario={scenario ?? undefined} />

          <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border/70 text-center text-xs">
            <div className="p-2.5 bg-slate-50 border border-slate-200/60 rounded-xl">
              <span className="text-slate-500 block text-[11px]">Required</span>
              <strong className="text-sm font-mono text-slate-900 font-bold">{run.metrics.total_required_positions}</strong>
            </div>
            <div className="p-2.5 bg-emerald-50/70 border border-emerald-200/60 rounded-xl">
              <span className="text-emerald-700 block text-[11px]">Filled</span>
              <strong className="text-sm font-mono text-emerald-800 font-bold">{run.metrics.total_filled_positions}</strong>
            </div>
            <div className="p-2.5 bg-red-50/70 border border-red-200/60 rounded-xl">
              <span className="text-red-700 block text-[11px]">Unfilled</span>
              <strong className="text-sm font-mono text-red-800 font-bold">{run.metrics.unfilled_positions}</strong>
            </div>
          </div>
        </div>

        {/* Workload Distribution Chart */}
        <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Employee Workload Distribution</h2>
            {run.metrics.workload_spread !== null && (
              <span className="text-xs text-slate-500 font-mono">
                Spread: {run.metrics.workload_spread.toFixed(1)}h
              </span>
            )}
          </div>
          <WorkloadChart metrics={run.metrics} />
        </div>
      </div>

      {/* Constraint Violations Panel */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-3 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Independent Constraint Verification</h2>
          <span className="text-xs font-mono text-slate-500">
            Violations: {run.violations?.length ?? 0}
          </span>
        </div>
        <ValidationPanel violations={run.violations || []} />
      </div>

      {/* Visual Timeline vs Tabular Roster Selector */}
      <div className="flex items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-slate-900">Staffing Dispatch Views</span>
        </div>
        <div className="flex items-center bg-slate-100 p-1 rounded-full border border-slate-200/80 text-xs">
          <button
            type="button"
            onClick={() => setDisplayMode('timeline')}
            className={clsx(
              'px-3.5 py-1 rounded-full font-medium transition-all flex items-center gap-1.5',
              displayMode === 'timeline' ? 'bg-slate-900 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <CalendarDaysIcon className="w-3.5 h-3.5" />
            Visual Timeline Planner
          </button>
          <button
            type="button"
            onClick={() => setDisplayMode('table')}
            className={clsx(
              'px-3.5 py-1 rounded-full font-medium transition-all flex items-center gap-1.5',
              displayMode === 'table' ? 'bg-slate-900 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <TableCellsIcon className="w-3.5 h-3.5" />
            Tabular Roster
          </button>
        </div>
      </div>

      {/* View 1: Workforce Timeline Planner (Centerpiece) */}
      {displayMode === 'timeline' && (
        <WorkforceTimelinePlanner
          assignments={run.assignments || []}
          scenario={scenario ?? undefined}
        />
      )}

      {/* View 2: Tabular Roster Table with Filters */}
      {displayMode === 'table' && (
        <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-4 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-border/70">
            <div>
              <h2 className="text-base font-bold text-slate-900">Staffing Roster Table</h2>
              <p className="text-xs text-slate-500">Shift assignments resolved by optimizer.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {/* Shift filter */}
              <select
                value={filterShift}
                onChange={e => setFilterShift(e.target.value)}
                className="px-3 py-1.5 border border-border/80 rounded-full bg-surface text-slate-800 text-xs shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="Filter by shift"
              >
                <option value="">All Shifts</option>
                {scenario?.shifts?.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
                ))}
              </select>

              {/* Unit filter */}
              <select
                value={filterUnit}
                onChange={e => setFilterUnit(e.target.value)}
                className="px-3 py-1.5 border border-border/80 rounded-full bg-surface text-slate-800 text-xs shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="Filter by production unit"
              >
                <option value="">All Production Units</option>
                {scenario?.units?.map(u => (
                  <option key={u.id} value={u.id}>{u.name} ({u.id})</option>
                ))}
              </select>

              {/* Employee filter */}
              <select
                value={filterEmployee}
                onChange={e => setFilterEmployee(e.target.value)}
                className="px-3 py-1.5 border border-border/80 rounded-full bg-surface text-slate-800 text-xs shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="Filter by employee"
              >
                <option value="">All Employees</option>
                {scenario?.employees?.map(e => (
                  <option key={e.id} value={e.id}>{e.name}</option>
                ))}
              </select>

              {(filterShift || filterUnit || filterEmployee) && (
                <button
                  type="button"
                  onClick={() => {
                    setFilterShift('');
                    setFilterUnit('');
                    setFilterEmployee('');
                  }}
                  className="text-xs text-slate-500 underline hover:text-slate-800 px-2"
                >
                  Reset filters
                </button>
              )}
            </div>
          </div>

          <RosterTable
            assignments={run.assignments || []}
            scenario={scenario ?? undefined}
            filterShift={filterShift}
            filterUnit={filterUnit}
            filterEmployee={filterEmployee}
          />
        </div>
      )}
    </div>
  );
}
