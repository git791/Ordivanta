'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { ScenarioSummary, RunSummary, HealthResponse } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import KpiCard from '@/components/ui/KpiCard';
import StatusBadge from '@/components/ui/StatusBadge';
import DataTable, { Column } from '@/components/ui/DataTable';
import EmptyState from '@/components/ui/EmptyState';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);
  const [sampleMessage, setSampleMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosData, runsData, healthData] = await Promise.all([
        api.getScenarios().catch(err => {
          console.error('getScenarios failed', err);
          return [] as ScenarioSummary[];
        }),
        api.getRuns().catch(err => {
          console.error('getRuns failed', err);
          return [] as RunSummary[];
        }),
        api.health().catch(err => {
          console.error('health check failed', err);
          return null;
        }),
      ]);

      if (!scenariosData && !runsData && !healthData) {
        throw new Error('Failed to connect to backend service.');
      }

      setScenarios(scenariosData || []);
      setRuns(runsData || []);
      setHealth(healthData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to the backend API.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setSampleMessage(null);
    try {
      await api.loadSample();
      setSampleMessage('Sample scenario loaded successfully.');
      await fetchData();
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to load sample scenario.');
    } finally {
      setLoadingSample(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading dashboard data…" />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Operations Dashboard" description="Workforce scheduling overview and recent optimization runs." />
        <ErrorBanner title="Connection Error" message={error} />
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  const latestRun = runs.length > 0 ? runs[0] : null;
  const totalEmployees = scenarios.reduce((acc, s) => acc + (s.employee_count || 0), 0);
  const totalDemand = scenarios.reduce((acc, s) => acc + (s.demand_count || 0), 0);

  const recentRuns = runs.slice(0, 5);

  const chartData = runs.slice(0, 10).reverse().map(r => ({
    id: r.run_id.slice(0, 8),
    coverage: Math.round(r.coverage_rate * 100),
    runtime: Number(r.runtime_seconds.toFixed(2)),
  }));

  const runColumns: Column<RunSummary>[] = [
    {
      key: 'run_id',
      header: 'Run ID',
      render: (r: RunSummary) => (
        <Link
          href={`/schedule/${r.run_id}`}
          className="font-mono text-primary hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
        >
          {r.run_id}
        </Link>
      ),
    },
    {
      key: 'algorithm',
      header: 'Algorithm',
      render: (r: RunSummary) => (
        <span className="font-mono text-xs uppercase px-2 py-0.5 bg-surface-muted rounded border border-border">
          {r.algorithm}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (r: RunSummary) => <StatusBadge status={r.status} size="sm" />,
    },
    {
      key: 'coverage_rate',
      header: 'Coverage',
      render: (r: RunSummary) => (
        <span className="font-mono tabular-nums">
          {(r.coverage_rate * 100).toFixed(1)}%
        </span>
      ),
      className: 'text-right',
    },
    {
      key: 'runtime_seconds',
      header: 'Solve Time',
      render: (r: RunSummary) => (
        <span className="font-mono tabular-nums">
          {r.runtime_seconds.toFixed(3)}s
        </span>
      ),
      className: 'text-right',
    },
    {
      key: 'created_at',
      header: 'Created At',
      render: (r: RunSummary) => (
        <span className="text-xs text-ink-muted">
          {new Date(r.created_at).toLocaleString()}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operations Dashboard"
        description="Workforce scheduling overview, solver status, and recent execution metrics."
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={handleLoadSample}
              disabled={loadingSample}
              className="px-3.5 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              {loadingSample ? 'Loading…' : 'Load Sample Scenario'}
            </button>
            <Link
              href="/schedule"
              className="px-3.5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              New Schedule Run
            </Link>
          </div>
        }
      />

      {sampleMessage && (
        <div className="bg-success-soft border border-success rounded-lg p-3 text-sm text-success flex items-center justify-between">
          <span>{sampleMessage}</span>
          <button
            onClick={() => setSampleMessage(null)}
            className="text-xs text-success underline ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Total Employees"
          value={totalEmployees}
          note={scenarios.length ? `Across ${scenarios.length} scenario${scenarios.length > 1 ? 's' : ''}` : 'No scenarios loaded'}
        />
        <KpiCard
          label="Positions Required"
          value={totalDemand}
          note="Total shift slots"
        />
        <KpiCard
          label="Latest Coverage Rate"
          value={latestRun ? `${(latestRun.coverage_rate * 100).toFixed(1)}%` : '—'}
          note={latestRun ? `Run: ${latestRun.run_id.slice(0, 8)}` : 'No runs executed'}
        />
        <KpiCard
          label="Latest Solver Status"
          value={latestRun ? <StatusBadge status={latestRun.status} size="sm" /> : '—'}
          note={latestRun ? `Algorithm: ${latestRun.algorithm.toUpperCase()}` : 'Awaiting first run'}
        />
        <KpiCard
          label="Latest Solve Time"
          value={latestRun ? `${latestRun.runtime_seconds.toFixed(3)}s` : '—'}
          note="Wall-clock time"
        />
      </div>

      {/* Coverage Trend Chart */}
      {chartData.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium text-ink uppercase tracking-wide mb-4">
            Recent Runs Coverage Trend (%)
          </h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
                <XAxis dataKey="id" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(val: unknown) => [`${val}%`, 'Coverage']} />
                <Bar dataKey="coverage" fill="#245A81" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Runs Table */}
      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-ink">Recent Schedule Runs</h2>
          {runs.length > 5 && (
            <Link href="/schedule" className="text-xs text-primary font-medium hover:underline">
              View all ({runs.length})
            </Link>
          )}
        </div>
        {runs.length === 0 ? (
          <EmptyState
            title="No schedule runs yet"
            description="Create a new schedule run or load sample data to test optimization."
            action={
              <Link
                href="/schedule"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
              >
                Start Schedule Run
              </Link>
            }
          />
        ) : (
          <DataTable<RunSummary>
            columns={runColumns}
            data={recentRuns}
            keyField="run_id"
            emptyMessage="No runs available."
          />
        )}
      </div>
    </div>
  );
}
