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
      header: 'Cell / Unit ID',
      render: (u: ProductionUnit) => (
        <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
          {u.id}
        </span>
      ),
    },
    {
      key: 'name',
      header: 'Workstation / Cell Name',
      render: (u: ProductionUnit) => (
        <span className="font-semibold text-slate-900 text-sm">{u.name}</span>
      ),
    },
    {
      key: 'required_skills',
      header: 'Mandatory Qualifications & Certifications',
      render: (u: ProductionUnit) => (
        <div className="flex flex-wrap gap-1.5">
          {u.required_skills.length === 0 ? (
            <span className="text-xs text-slate-400 italic">No specific qualifications required</span>
          ) : (
            u.required_skills.map((s, idx) => (
              <span
                key={idx}
                className="inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full bg-purple-50 text-purple-700 border border-purple-200/80 shadow-2xs"
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
        title="Production Units & Cells"
        description="Configured workstations, manufacturing stations, and qualification requirements."
      />

      {units.length === 0 ? (
        <div className="bg-surface border border-border/80 rounded-3xl p-8 shadow-sm">
          <EmptyState
            title="No production units registered"
            description="Production units define the stations and qualified skill demands of your plant."
            action={
              <button
                onClick={handleLoadSample}
                disabled={loadingSample}
                className="px-5 py-2.5 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50 shadow-2xs"
              >
                {loadingSample ? 'Loading…' : 'Load Sample Scenario'}
              </button>
            }
          />
        </div>
      ) : (
        <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm overflow-hidden">
          <div className="rounded-2xl border border-border/70 overflow-hidden">
            <DataTable<ProductionUnit>
              columns={columns}
              data={units}
              keyField="id"
              emptyMessage="No production units available."
            />
          </div>
        </div>
      )}
    </div>
  );
}
