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
        <span className="font-semibold text-slate-900">{e.name}</span>
      ),
    },
    {
      key: 'skills',
      header: 'Qualifications / Skills',
      render: (e: Employee) => (
        <div className="flex flex-wrap gap-1.5">
          {e.skills.map((s, idx) => (
            <span
              key={idx}
              className="inline-block px-2.5 py-0.5 text-xs font-medium rounded-full bg-purple-50 text-purple-700 border border-purple-200/80 shadow-2xs"
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
        <span className="font-mono text-xs tabular-nums text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
          {e.available_shifts.length} shift{e.available_shifts.length === 1 ? '' : 's'}
        </span>
      ),
    },
    {
      key: 'max_hours',
      header: 'Max Scheduled Hours',
      render: (e: Employee) => (
        <span className="font-mono font-semibold text-xs tabular-nums text-slate-900">{e.max_hours}h</span>
      ),
      className: 'text-right',
    },
    {
      key: 'id',
      header: 'ID',
      render: (e: Employee) => (
        <span className="font-mono text-xs text-slate-400">{e.id}</span>
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
              className="px-4 py-2 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50 shadow-2xs"
            >
              {loadingSample ? 'Loading…' : 'Load Sample Scenario'}
            </button>
          ) : undefined
        }
      />

      {employees.length === 0 ? (
        <div className="bg-surface border border-border/80 rounded-3xl p-8 shadow-sm">
          <EmptyState
            title="No workforce records found"
            description="Load a scenario or add employees to get started."
            action={
              <button
                onClick={handleLoadSample}
                disabled={loadingSample}
                className="px-5 py-2.5 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50 shadow-2xs"
              >
                {loadingSample ? 'Loading sample…' : 'Load Sample Scenario'}
              </button>
            }
          />
        </div>
      ) : (
        <div className="bg-surface border border-border/80 rounded-3xl p-6 space-y-5 shadow-sm">
          {/* Active Scenario Selector */}
          {scenarios.length > 0 && (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border/70 gap-3">
              <div className="flex items-center gap-2.5">
                <label htmlFor="scenario-select" className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Active Scenario:
                </label>
                <select
                  id="scenario-select"
                  value={selectedScenarioId}
                  onChange={e => handleScenarioChange(e.target.value)}
                  className="px-3.5 py-1.5 border border-border/80 rounded-full text-xs font-medium bg-canvas text-slate-800 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {scenarios.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.employee_count} emp, {s.unit_count} units, {s.shift_count} shifts)
                    </option>
                  ))}
                </select>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                Showing {filteredEmployees.length} of {employees.length} employee{employees.length === 1 ? '' : 's'}
              </span>
            </div>
          )}

          {/* Search Bar & Available Skill Chips */}
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex flex-1 items-center gap-2 max-w-md">
                <input
                  id="search-filter"
                  type="text"
                  placeholder={
                    availableSkills.length > 0
                      ? `Filter name, ID, or skills (${availableSkills.slice(0, 3).join(', ')})...`
                      : 'Search by name, skill, or ID...'
                  }
                  value={searchFilter}
                  onChange={e => setSearchFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-border/80 rounded-full text-xs bg-canvas text-slate-900 placeholder:text-slate-400 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
                {searchFilter && (
                  <button
                    onClick={() => setSearchFilter('')}
                    className="text-xs text-slate-500 hover:text-slate-800 underline whitespace-nowrap px-2"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Quick-filter Skill Tags */}
            {availableSkills.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                <span className="text-slate-500 text-[11px] font-medium">Scenario Skills:</span>
                {availableSkills.map(s => {
                  const isSelected = searchFilter.toLowerCase() === s.toLowerCase();
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSearchFilter(isSelected ? '' : s)}
                      className={`px-3 py-1 rounded-full text-xs transition-all ${
                        isSelected
                          ? 'bg-slate-900 text-white font-semibold shadow-2xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'
                      }`}
                    >
                      {s} {isSelected ? '✕' : ''}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="overflow-hidden rounded-2xl border border-border/70">
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
        </div>
      )}
    </div>
  );
}
