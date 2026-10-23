'use client';

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Employee, ScenarioSummary, ScenarioResponse } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import DataTable, { Column } from '@/components/ui/DataTable';
import EmptyState from '@/components/ui/EmptyState';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';

export default function WorkforcePage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [skillFilter, setSkillFilter] = useState<string>('');
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosList, empList] = await Promise.all([
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
        api.getEmployees().catch(() => [] as Employee[]),
      ]);

      setScenarios(scenariosList || []);

      // If backend getEmployees is empty but we have scenarios, fetch first scenario's employees
      if ((!empList || empList.length === 0) && scenariosList && scenariosList.length > 0) {
        try {
          const sc: ScenarioResponse = await api.getScenario(scenariosList[0].id);
          setEmployees(sc.employees || []);
        } catch {
          setEmployees(empList || []);
        }
      } else {
        setEmployees(empList || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workforce data.';
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
      setError('Failed to load sample scenario');
    } finally {
      setLoadingSample(false);
    }
  };

  const filteredEmployees = useMemo(() => {
    if (!skillFilter.trim()) return employees;
    const filter = skillFilter.toLowerCase().trim();
    return employees.filter(emp =>
      emp.skills.some(s => s.toLowerCase().includes(filter))
    );
  }, [employees, skillFilter]);

  if (loading) {
    return <LoadingSpinner label="Loading workforce registry…" />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Workforce Management" description="Registered personnel, qualification profiles, and availability." />
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

  const columns: Column<Employee>[] = [
    {
      key: 'name',
      header: 'Employee Name',
      render: (e: Employee) => (
        <span className="font-medium text-ink">{e.name}</span>
      ),
    },
    {
      key: 'skills',
      header: 'Qualifications / Skills',
      render: (e: Employee) => (
        <div className="flex flex-wrap gap-1">
          {e.skills.map((s, idx) => (
            <span
              key={idx}
              className="inline-block px-2 py-0.5 text-xs rounded bg-surface-muted border border-border text-ink-muted"
            >
              {s}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'available_shifts',
      header: 'Available Shifts',
      render: (e: Employee) => (
        <span className="font-mono text-xs tabular-nums text-ink">
          {e.available_shifts.length} shift{e.available_shifts.length === 1 ? '' : 's'}
        </span>
      ),
    },
    {
      key: 'max_hours',
      header: 'Max Scheduled Hours',
      render: (e: Employee) => (
        <span className="font-mono tabular-nums">{e.max_hours}h</span>
      ),
      className: 'text-right',
    },
    {
      key: 'id',
      header: 'ID',
      render: (e: Employee) => (
        <span className="font-mono text-xs text-ink-muted">{e.id}</span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workforce Management"
        description="Personnel profiles, qualified skills, and shift availability limits."
        action={
          employees.length === 0 ? (
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

      {employees.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-6">
          <EmptyState
            title="No workforce records found"
            description="Load a scenario or add employees to get started."
            action={
              <button
                onClick={handleLoadSample}
                disabled={loadingSample}
                className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
              >
                {loadingSample ? 'Loading sample…' : 'Load Sample Scenario'}
              </button>
            }
          />
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg p-5 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label htmlFor="skill-filter" className="text-sm font-medium text-ink">
                Filter by Skill:
              </label>
              <input
                id="skill-filter"
                type="text"
                placeholder="e.g. welding, assembly"
                value={skillFilter}
                onChange={e => setSkillFilter(e.target.value)}
                className="px-3 py-1.5 border border-border rounded text-sm bg-surface text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              />
              {skillFilter && (
                <button
                  onClick={() => setSkillFilter('')}
                  className="text-xs text-ink-muted hover:text-ink underline"
                >
                  Clear
                </button>
              )}
            </div>
            <span className="text-xs text-ink-muted">
              Showing {filteredEmployees.length} of {employees.length} employee{employees.length === 1 ? '' : 's'}
            </span>
          </div>

          <DataTable<Employee>
            columns={columns}
            data={filteredEmployees}
            keyField="id"
            emptyMessage="No employees matched the specified skill filter."
          />
        </div>
      )}
    </div>
  );
}
