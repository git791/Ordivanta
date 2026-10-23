'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { SolveResponse, ScenarioResponse } from '@/lib/types';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import RosterTable from '@/components/schedule/RosterTable';
import CoverageChart from '@/components/schedule/CoverageChart';
import WorkloadChart from '@/components/schedule/WorkloadChart';
import ValidationPanel from '@/components/schedule/ValidationPanel';
import { InformationCircleIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function ScheduleRunDetailsPage() {
  const params = useParams();
  const runId = params?.runId as string;

  const [run, setRun] = useState<SolveResponse | null>(null);
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
          className="inline-block px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
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
    <div className="space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-ink-muted">
          <Link href="/dashboard" className="hover:underline">Dashboard</Link>
          <span>/</span>
          <Link href="/schedule" className="hover:underline">Schedule</Link>
          <span>/</span>
          <span className="font-mono text-ink font-semibold">{run.run_id}</span>
        </div>
        <Link
          href="/schedule"
          className="text-primary hover:underline text-xs font-medium"
        >
          + New Schedule Run
        </Link>
      </div>

      {/* Header Banner */}
      <div className="bg-surface border border-border rounded-lg p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-bold font-mono text-ink tracking-tight">{run.run_id}</h1>
            <StatusBadge status={run.status} />
            <span className="font-mono text-xs uppercase px-2.5 py-1 bg-surface-muted rounded border border-border text-ink font-semibold">
              {run.algorithm}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-ink-muted">
            <span>
              Scenario:{' '}
              <strong className="text-ink font-medium">
                {scenario?.name ?? run.scenario_id}
              </strong>
            </span>
            <span>•</span>
            <span>
              Run Time:{' '}
              <strong className="text-ink font-mono">{run.runtime_seconds.toFixed(3)}s</strong>
            </span>
            <span>•</span>
            <span>
              Executed:{' '}
              <strong className="text-ink">{new Date(run.created_at).toLocaleString()}</strong>
            </span>
            {run.objective_value !== null && (
              <>
                <span>•</span>
                <span>
                  Objective:{' '}
                  <strong className="text-ink font-mono">{run.objective_value.toFixed(2)}</strong>
                </span>
              </>
            )}
          </div>
        </div>

        <div>
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={!isExportable}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
              isExportable
                ? 'bg-primary text-white hover:bg-primary-hover cursor-pointer'
                : 'bg-surface-muted text-ink-muted border border-border cursor-not-allowed opacity-60'
            }`}
            title={isExportable ? 'Export schedule assignments to CSV' : 'Export only available for OPTIMAL or FEASIBLE status'}
          >
            <ArrowDownTrayIcon className="w-4 h-4 shrink-0" aria-hidden="true" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Warnings List (if any) */}
      {run.warnings && run.warnings.length > 0 && (
        <div className="bg-primary-soft/60 border border-primary/30 rounded-lg p-4 flex items-start gap-3">
          <InformationCircleIcon className="w-5 h-5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-primary">Schedule Warnings</p>
            <ul className="mt-1 list-disc list-inside text-xs text-ink space-y-0.5">
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
        <div className="bg-surface border border-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">Coverage & Headcount</h2>
            <span className="font-mono font-bold text-lg text-primary">
              {(run.metrics.coverage_rate * 100).toFixed(1)}%
            </span>
          </div>

          <CoverageChart metrics={run.metrics} scenario={scenario ?? undefined} />

          <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border text-center text-xs">
            <div className="p-2 bg-surface-muted rounded">
              <span className="text-ink-muted block">Required</span>
              <strong className="text-sm font-mono text-ink">{run.metrics.total_required_positions}</strong>
            </div>
            <div className="p-2 bg-surface-muted rounded">
              <span className="text-ink-muted block">Filled</span>
              <strong className="text-sm font-mono text-success">{run.metrics.total_filled_positions}</strong>
            </div>
            <div className="p-2 bg-surface-muted rounded">
              <span className="text-ink-muted block">Unfilled</span>
              <strong className="text-sm font-mono text-danger">{run.metrics.unfilled_positions}</strong>
            </div>
          </div>
        </div>

        {/* Workload Distribution Chart */}
        <div className="bg-surface border border-border rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink">Employee Workload Distribution</h2>
            {run.metrics.workload_spread !== null && (
              <span className="text-xs text-ink-muted font-mono">
                Spread: {run.metrics.workload_spread.toFixed(1)}h
              </span>
            )}
          </div>
          <WorkloadChart metrics={run.metrics} />
        </div>
      </div>

      {/* Constraint Violations Panel */}
      <div className="bg-surface border border-border rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">Validation & Constraint Verification</h2>
          <span className="text-xs font-mono text-ink-muted">
            Violations: {run.violations?.length ?? 0}
          </span>
        </div>
        <ValidationPanel violations={run.violations || []} />
      </div>

      {/* Roster Table with Filters */}
      <div className="bg-surface border border-border rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">Staffing Roster Table</h2>
            <p className="text-xs text-ink-muted">Shift assignments resolved by optimizer.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Shift filter */}
            <select
              value={filterShift}
              onChange={e => setFilterShift(e.target.value)}
              className="px-2.5 py-1.5 border border-border rounded bg-surface text-ink text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
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
              className="px-2.5 py-1.5 border border-border rounded bg-surface text-ink text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
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
              className="px-2.5 py-1.5 border border-border rounded bg-surface text-ink text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
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
                className="text-xs text-ink-muted underline hover:text-ink px-1"
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
    </div>
  );
}
