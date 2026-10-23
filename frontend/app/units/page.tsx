'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { ProductionUnit, ScenarioResponse, ScenarioSummary } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import DataTable, { Column } from '@/components/ui/DataTable';
import EmptyState from '@/components/ui/EmptyState';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';

export default function UnitsPage() {
  const [units, setUnits] = useState<ProductionUnit[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [unitsList, scenariosList] = await Promise.all([
        api.getUnits().catch(() => [] as ProductionUnit[]),
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
      ]);

      if ((!unitsList || unitsList.length === 0) && scenariosList && scenariosList.length > 0) {
        try {
          const sc: ScenarioResponse = await api.getScenario(scenariosList[0].id);
          setUnits(sc.units || []);
        } catch {
          setUnits(unitsList || []);
        }
      } else {
        setUnits(unitsList || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch production units.';
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
    return <LoadingSpinner label="Loading production units…" />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Production Units" description="Operational workstations, assembly lines, and skill prerequisites." />
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

  const columns: Column<ProductionUnit>[] = [
    {
      key: 'id',
      header: 'Unit ID',
      render: (u: ProductionUnit) => (
        <span className="font-mono text-xs font-semibold text-ink">{u.id}</span>
      ),
    },
    {
      key: 'name',
      header: 'Unit Name / Station',
      render: (u: ProductionUnit) => (
        <span className="font-medium text-ink">{u.name}</span>
      ),
    },
    {
      key: 'required_skills',
      header: 'Required Qualifications',
      render: (u: ProductionUnit) => (
        <div className="flex flex-wrap gap-1">
          {u.required_skills.length === 0 ? (
            <span className="text-xs text-ink-muted">No specific qualifications required</span>
          ) : (
            u.required_skills.map((s, idx) => (
              <span
                key={idx}
                className="inline-block px-2 py-0.5 text-xs rounded bg-surface-muted border border-border text-ink-muted"
              >
                {s}
              </span>
            ))
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Production Units"
        description="Configured workstations, manufacturing stations, and required qualifications."
      />

      {units.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-6">
          <EmptyState
            title="No production units registered"
            description="Production units define the stations and qualified skill demands of your plant."
            action={
              <button
                onClick={handleLoadSample}
                disabled={loadingSample}
                className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
              >
                {loadingSample ? 'Loading…' : 'Load Sample Scenario'}
              </button>
            }
          />
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg p-5">
          <DataTable<ProductionUnit>
            columns={columns}
            data={units}
            keyField="id"
            emptyMessage="No production units available."
          />
        </div>
      )}
    </div>
  );
}
