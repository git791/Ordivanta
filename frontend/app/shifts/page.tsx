'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Shift, Demand, ScenarioSummary, ScenarioResponse } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import DataTable, { Column } from '@/components/ui/DataTable';
import EmptyState from '@/components/ui/EmptyState';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';

interface DemandRow extends Demand {
  scenario_name?: string;
}

export default function ShiftsPage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [demands, setDemands] = useState<DemandRow[]>([]);
  const [, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [shiftsList, scenariosList] = await Promise.all([
        api.getShifts().catch(() => [] as Shift[]),
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
      ]);

      setScenarios(scenariosList || []);

      let allShifts = shiftsList || [];
      const allDemands: DemandRow[] = [];

      if (scenariosList && scenariosList.length > 0) {
        // Fetch detailed scenario data to populate shifts and demands
        const scenarioDetails = await Promise.all(
          scenariosList.map(s => api.getScenario(s.id).catch(() => null))
        );

        for (const detail of scenarioDetails) {
          if (!detail) continue;
          if (allShifts.length === 0 && detail.shifts) {
            allShifts = detail.shifts;
          }
          if (detail.demands) {
            detail.demands.forEach(d => {
              allDemands.push({
                ...d,
                scenario_name: detail.name,
              });
            });
          }
        }
      }

      setShifts(allShifts);
      setDemands(allDemands);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch shift and demand data.';
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
    try {
      await api.loadSample();
      await fetchData();
    } catch {
      setError('Failed to load sample scenario.');
    } finally {
      setLoadingSample(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading shift definitions and demand matrix…" />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Shift Definitions & Demand" description="Operational shift windows and station staffing requirements." />
        <ErrorBanner title="Data Load Error" message={error} />
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const shiftColumns: Column<Shift>[] = [
    {
      key: 'id',
      header: 'Shift ID',
      render: (s: Shift) => <span className="font-mono text-xs font-semibold text-ink">{s.id}</span>,
    },
    {
      key: 'name',
      header: 'Shift Name',
      render: (s: Shift) => <span className="font-medium text-ink">{s.name}</span>,
    },
    {
      key: 'start_time',
      header: 'Start Time',
      render: (s: Shift) => <span className="font-mono text-xs tabular-nums text-ink">{s.start_time}</span>,
    },
    {
      key: 'end_time',
      header: 'End Time',
      render: (s: Shift) => <span className="font-mono text-xs tabular-nums text-ink">{s.end_time}</span>,
    },
    {
      key: 'duration_hours',
      header: 'Duration',
      render: (s: Shift) => <span className="font-mono tabular-nums">{s.duration_hours.toFixed(1)}h</span>,
      className: 'text-right',
    },
  ];

  const demandColumns: Column<DemandRow>[] = [
    {
      key: 'unit_id',
      header: 'Production Unit ID',
      render: (d: DemandRow) => <span className="font-mono text-xs font-semibold text-ink">{d.unit_id}</span>,
    },
    {
      key: 'shift_id',
      header: 'Shift ID',
      render: (d: DemandRow) => <span className="font-mono text-xs text-ink">{d.shift_id}</span>,
    },
    {
      key: 'required_headcount',
      header: 'Required Headcount',
      render: (d: DemandRow) => (
        <span className="font-mono font-semibold tabular-nums text-ink">
          {d.required_headcount} operator{d.required_headcount === 1 ? '' : 's'}
        </span>
      ),
      className: 'text-right',
    },
    {
      key: 'scenario_name',
      header: 'Scenario',
      render: (d: DemandRow) => (
        <span className="text-xs text-ink-muted">{d.scenario_name ?? '—'}</span>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Shift Definitions & Demand"
        description="Shift operational windows and required headcount demand per production unit."
        action={
          shifts.length === 0 ? (
            <button
              onClick={handleLoadSample}
              disabled={loadingSample}
              className="px-3.5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
            >
              {loadingSample ? 'Loading…' : 'Load Sample Scenario'}
            </button>
          ) : undefined
        }
      />

      {/* Section 1: Shift Definitions */}
      <section className="bg-surface border border-border rounded-lg p-5 space-y-4">
        <div>
          <h2 className="text-base font-semibold text-ink">1. Shift Windows</h2>
          <p className="text-xs text-ink-muted mt-0.5">Operating schedule windows and duration hours.</p>
        </div>
        {shifts.length === 0 ? (
          <EmptyState
            title="No shift definitions registered"
            description="Shifts define working hours and operating time windows for the plant."
          />
        ) : (
          <DataTable<Shift>
            columns={shiftColumns}
            data={shifts}
            keyField="id"
            emptyMessage="No shift definitions available."
          />
        )}
      </section>

      {/* Section 2: Demand Summary */}
      <section className="bg-surface border border-border rounded-lg p-5 space-y-4">
        <div>
          <h2 className="text-base font-semibold text-ink">2. Station Headcount Demand</h2>
          <p className="text-xs text-ink-muted mt-0.5">Staffing requirements by production unit and shift.</p>
        </div>
        {demands.length === 0 ? (
          <EmptyState
            title="No shift demand entries found"
            description="Demand defines how many qualified operators each unit requires for a given shift."
          />
        ) : (
          <DataTable<DemandRow>
            columns={demandColumns}
            data={demands}
            getRowKey={(d, idx) => `${d.unit_id}-${d.shift_id}-${d.scenario_name}-${idx}`}
            emptyMessage="No demand entries found."
          />
        )}
      </section>
    </div>
  );
}
