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
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  const loadScenarioEmployees = useCallback(async (scenarioId: string) => {
    try {
      setLoading(true);
      setError(null);
      const sc: ScenarioResponse = await api.getScenario(scenarioId);
      setEmployees(sc.employees || []);
      setSelectedScenarioId(scenarioId);
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to load workforce for selected scenario.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosList, empList] = await Promise.all([
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
        api.getEmployees().catch(() => [] as Employee[]),
      ]);

      const scList = scenariosList || [];
      setScenarios(scList);

      if (scList.length > 0) {
        const activeId = selectedScenarioId || scList[0].id;
        setSelectedScenarioId(activeId);
        try {
          const sc: ScenarioResponse = await api.getScenario(activeId);
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
  }, [selectedScenarioId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId);
    setSearchFilter('');
    loadScenarioEmployees(scenarioId);
  };

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

  const availableSkills = useMemo(() => {
    const set = new Set<string>();
    employees.forEach(emp => emp.skills.forEach(s => set.add(s)));
    return Array.from(set).sort();
  }, [employees]);

  const filteredEmployees = useMemo(() => {
    if (!searchFilter.trim()) return employees;
    const q = searchFilter.toLowerCase().trim();
    return employees.filter(emp =>
      emp.name.toLowerCase().includes(q) ||
      emp.id.toLowerCase().includes(q) ||
      emp.skills.some(s => s.toLowerCase().includes(q)) ||
      `${emp.max_hours}h`.toLowerCase().includes(q)
    );
  }, [employees, searchFilter]);

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
          {/* Active Scenario Selector */}
          {scenarios.length > 0 && (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-3">
              <div className="flex items-center gap-2">
                <label htmlFor="scenario-select" className="text-xs font-semibold uppercase text-ink">
                  Active Scenario:
                </label>
                <select
                  id="scenario-select"
                  value={selectedScenarioId}
                  onChange={e => handleScenarioChange(e.target.value)}
                  className="px-3 py-1.5 border border-border rounded text-sm bg-surface text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                >
                  {scenarios.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.employee_count} emp, {s.unit_count} units, {s.shift_count} shifts)
                    </option>
                  ))}
                </select>
              </div>
              <span className="text-xs text-ink-muted">
                Showing {filteredEmployees.length} of {employees.length} employee{employees.length === 1 ? '' : 's'}
              </span>
            </div>
          )}

          {/* Search Bar & Available Skill Chips */}
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex flex-1 items-center gap-2 max-w-md">
                <label htmlFor="search-filter" className="text-sm font-medium text-ink whitespace-nowrap">
                  Search Workforce:
                </label>
                <input
                  id="search-filter"
                  type="text"
                  placeholder={
                    availableSkills.length > 0
                      ? `Search name, ID, or skills (e.g. ${availableSkills.slice(0, 3).join(', ')})...`
                      : 'Search by name, skill, or ID...'
                  }
                  value={searchFilter}
                  onChange={e => setSearchFilter(e.target.value)}
                  className="w-full px-3 py-1.5 border border-border rounded text-sm bg-surface text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                />
                {searchFilter && (
                  <button
                    onClick={() => setSearchFilter('')}
                    className="text-xs text-ink-muted hover:text-ink underline whitespace-nowrap"
                  >
                    Clear
                  </button>
                )}
              </div>
              {scenarios.length === 0 && (
                <span className="text-xs text-ink-muted">
                  Showing {filteredEmployees.length} of {employees.length} employee{employees.length === 1 ? '' : 's'}
                </span>
              )}
            </div>

            {/* Quick-filter Skill Tags */}
            {availableSkills.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                <span className="text-ink-muted font-medium">Skills in this scenario:</span>
                {availableSkills.map(s => {
                  const isSelected = searchFilter.toLowerCase() === s.toLowerCase();
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSearchFilter(isSelected ? '' : s)}
                      className={`px-2 py-0.5 rounded border transition-colors ${
                        isSelected
                          ? 'bg-primary text-white border-primary font-medium'
                          : 'bg-surface-muted text-ink border-border hover:bg-surface-muted/80'
                      }`}
                    >
                      {s} {isSelected ? '✕' : ''}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <DataTable<Employee>
            columns={columns}
            data={filteredEmployees}
            keyField="id"
            emptyMessage={
              searchFilter
                ? `No employees matched "${searchFilter}". Available skills in this scenario: ${
                    availableSkills.length > 0 ? availableSkills.join(', ') : 'None'
                  }.`
                : 'No employees found in this scenario.'
            }
          />
        </div>
      )}
    </div>
  );
}
