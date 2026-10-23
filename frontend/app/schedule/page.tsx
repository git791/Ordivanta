'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type {
  ScenarioSummary,
  ScenarioResponse,
  Algorithm,
  ObjectiveConfig,
  ValidationResponse,
  SolveRequest,
  Violation,
  Employee,
  DatasetMetadata,
  InstanceSummary,
} from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import DataTable, { Column } from '@/components/ui/DataTable';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import ValidationPanel from '@/components/schedule/ValidationPanel';

const STEP_LABELS = [
  '1. Scenario',
  '2. Workforce',
  '3. Unit Demand',
  '4. Algorithm & Objective',
  '5. Validate & Review',
  '6. Running',
];

export default function ScheduleBuilderPage() {
  const router = useRouter();

  // Stepper state
  const [step, setStep] = useState<number>(1);
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioResponse | null>(null);
  const [loadingScenario, setLoadingScenario] = useState<boolean>(false);

  // Benchmark Datasets state
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('synthetic_manufacturing');
  const [instances, setInstances] = useState<InstanceSummary[]>([]);
  const [selectedInstanceId, setSelectedInstanceId] = useState<string>('');
  const [loadingInstances, setLoadingInstances] = useState<boolean>(false);
  const [loadingBenchmark, setLoadingBenchmark] = useState<boolean>(false);
  const [loadedInstanceSummary, setLoadedInstanceSummary] = useState<InstanceSummary | null>(null);

  // Configuration state
  const [algorithm, setAlgorithm] = useState<Algorithm>('milp');
  const [objective, setObjective] = useState<ObjectiveConfig>({
    primary: 'feasibility',
    include_assignment_cost: false,
    fairness_weight: 0,
  });
  const [timeLimitSeconds, setTimeLimitSeconds] = useState<number>(60);

  // Validation & Execution state
  const [validationResult, setValidationResult] = useState<ValidationResponse | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingInit, setLoadingInit] = useState<boolean>(true);

  // Load scenarios list on mount
  const fetchScenarios = useCallback(async () => {
    try {
      const data = await api.getScenarios();
      setScenarios(data || []);
      if (data && data.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(data[0].id);
      }
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to fetch scenarios list.');
    } finally {
      setLoadingInit(false);
    }
  }, [selectedScenarioId]);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  // Load scenario details when selectedScenarioId changes
  useEffect(() => {
    if (!selectedScenarioId) {
      setSelectedScenario(null);
      return;
    }
    let isCancelled = false;
    setLoadingScenario(true);
    api.getScenario(selectedScenarioId)
      .then(sc => {
        if (!isCancelled) setSelectedScenario(sc);
      })
      .catch(err => {
        if (!isCancelled) {
          console.error(err);
          setError('Failed to load details for selected scenario.');
        }
      })
      .finally(() => {
        if (!isCancelled) setLoadingScenario(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedScenarioId]);

  // Load available datasets
  useEffect(() => {
    api.getDatasets()
      .then(data => setDatasets(data || []))
      .catch(err => console.error('Failed to load datasets metadata:', err));
  }, []);

  // Load instances when selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    setLoadingInstances(true);
    api.getDatasetInstances(selectedDatasetId)
      .then(insts => {
        setInstances(insts || []);
        if (insts && insts.length > 0) {
          setSelectedInstanceId(insts[0].instance_id);
        } else {
          setSelectedInstanceId('');
        }
      })
      .catch(err => console.error('Failed to load dataset instances:', err))
      .finally(() => setLoadingInstances(false));
  }, [selectedDatasetId]);

  // Load selected benchmark instance into active scenario
  const handleLoadBenchmark = async () => {
    if (!selectedDatasetId || !selectedInstanceId) return;
    setLoadingBenchmark(true);
    setError(null);
    try {
      const res = await api.loadDatasetInstance(selectedDatasetId, selectedInstanceId);
      await fetchScenarios();
      setSelectedScenarioId(res.scenario.id);
      setSelectedScenario(res.scenario);
      setLoadedInstanceSummary(res.instance_summary);
    } catch (err: unknown) {
      console.error('Failed to load benchmark instance:', err);
      setError('Failed to import benchmark instance.');
    } finally {
      setLoadingBenchmark(false);
    }
  };

  // Validate scenario on Step 5
  const runValidation = useCallback(async (scenarioId: string) => {
    setIsValidating(true);
    setValidationResult(null);
    try {
      const res = await api.validateScenario(scenarioId);
      setValidationResult(res);
    } catch (err: unknown) {
      console.error(err);
      setValidationResult({
        is_valid: false,
        errors: [{
          code: 'VALIDATION_REQUEST_FAILED',
          message: err instanceof Error ? err.message : 'Validation request failed.',
          field: null,
          entity_id: null,
          severity: 'error',
        }],
        warnings: [],
      });
    } finally {
      setIsValidating(false);
    }
  }, []);

  const handleNextFromStep4 = async () => {
    if (selectedScenarioId) {
      setStep(5);
      await runValidation(selectedScenarioId);
    }
  };

  const handleRunSchedule = async () => {
    if (!selectedScenarioId) return;
    setStep(6);
    setIsRunning(true);
    setError(null);

    const payload: SolveRequest = {
      scenario_id: selectedScenarioId,
      algorithm,
      objective,
      time_limit_seconds: timeLimitSeconds,
    };

    try {
      const response = await api.solve(payload);
      if (response && response.run_id) {
        router.push(`/schedule/${response.run_id}`);
      } else {
        throw new Error('Solver completed without returning a run_id.');
      }
    } catch (err: unknown) {
      console.error('Solve failed:', err);
      setIsRunning(false);
      if (typeof err === 'object' && err !== null && 'errors' in err) {
        const apiErr = err as { errors?: Array<{ message: string }> };
        const msg = apiErr.errors?.map(e => e.message).join(', ') || 'Failed to solve schedule.';
        setError(msg);
      } else {
        setError(err instanceof Error ? err.message : 'Solver failed to execute schedule.');
      }
    }
  };

  const handleLoadSample = async () => {
    try {
      setLoadingScenario(true);
      const sample = await api.loadSample();
      await fetchScenarios();
      setSelectedScenarioId(sample.id);
      setSelectedScenario(sample);
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to load sample scenario.');
    } finally {
      setLoadingScenario(false);
    }
  };

  // Convert validation issues to violations for ValidationPanel
  const violations: Violation[] = useMemo(() => {
    if (!validationResult) return [];
    const list: Violation[] = [];
    (validationResult.errors || []).forEach(e => {
      list.push({
        code: e.code,
        message: e.message,
        severity: 'error',
        employee_id: e.entity_id,
        unit_id: null,
        shift_id: null,
      });
    });
    (validationResult.warnings || []).forEach(w => {
      list.push({
        code: w.code,
        message: w.message,
        severity: 'warning',
        employee_id: w.entity_id,
        unit_id: null,
        shift_id: null,
      });
    });
    return list;
  }, [validationResult]);

  // Total required positions calculation
  const totalDemand = useMemo(() => {
    if (!selectedScenario?.demands) return 0;
    return selectedScenario.demands.reduce((acc, d) => acc + d.required_headcount, 0);
  }, [selectedScenario]);

  if (loadingInit) {
    return <LoadingSpinner label="Loading scheduling wizard…" />;
  }

  const employeeColumns: Column<Employee>[] = [
    { key: 'name', header: 'Name', render: (e: Employee) => <span className="font-medium text-ink">{e.name}</span> },
    { key: 'skills', header: 'Skills', render: (e: Employee) => e.skills.join(', ') },
    { key: 'available_shifts', header: 'Available Shifts', render: (e: Employee) => `${e.available_shifts.length} shifts` },
    { key: 'max_hours', header: 'Max Hours', render: (e: Employee) => `${e.max_hours}h`, className: 'text-right font-mono' },
  ];

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Schedule Builder"
        description="Configure scenario parameters, select optimization algorithm, and solve workforce schedules."
      />

      {/* Stepper Header */}
      <nav aria-label="Progress" className="bg-surface border border-border rounded-lg p-3">
        <ol className="flex items-center justify-between gap-2 overflow-x-auto">
          {STEP_LABELS.map((label, idx) => {
            const stepNum = idx + 1;
            const isCurrent = step === stepNum;
            const isCompleted = step > stepNum;
            return (
              <li key={label} className="flex-1 min-w-[120px]">
                <div
                  className={`flex items-center gap-2 px-3 py-2 text-xs font-medium rounded transition-colors ${
                    isCurrent
                      ? 'bg-primary-soft text-primary border border-primary'
                      : isCompleted
                      ? 'text-success bg-success-soft/50'
                      : 'text-ink-muted'
                  }`}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  <span
                    className={`w-5 h-5 flex items-center justify-center rounded-full text-xs font-bold ${
                      isCurrent
                        ? 'bg-primary text-white'
                        : isCompleted
                        ? 'bg-success text-white'
                        : 'bg-surface-muted text-steel'
                    }`}
                  >
                    {isCompleted ? '✓' : stepNum}
                  </span>
                  <span className="truncate">{label}</span>
                </div>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* STEP 1: Scenario Selection */}
      {step === 1 && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-ink">Step 1 — Select Scenario</h2>
            <p className="text-sm text-ink-muted mt-1">
              Select an existing manufacturing scenario or load the reference sample scenario.
            </p>
          </div>

          <div className="space-y-4 max-w-xl">
            <div>
              <label htmlFor="scenario-select" className="block text-sm font-medium text-ink mb-1">
                Active Scenario:
              </label>
              <select
                id="scenario-select"
                value={selectedScenarioId ?? ''}
                onChange={e => setSelectedScenarioId(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-surface text-ink text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              >
                {scenarios.length === 0 && <option value="">No scenarios found</option>}
                {scenarios.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.employee_count} employees, {s.unit_count} units, {s.shift_count} shifts)
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={handleLoadSample}
                disabled={loadingScenario}
                className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors disabled:opacity-50"
              >
                {loadingScenario ? 'Loading Sample…' : 'Load Sample Scenario'}
              </button>
            </div>

            {selectedScenario && (
              <div className="p-4 bg-surface-muted rounded border border-border space-y-1 text-sm">
                <p className="font-semibold text-ink">{selectedScenario.name}</p>
                <p className="text-ink-muted">Scenario ID: <span className="font-mono text-xs">{selectedScenario.id}</span></p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs font-mono">
                  <div>Employees: {selectedScenario.employees?.length ?? 0}</div>
                  <div>Units: {selectedScenario.units?.length ?? 0}</div>
                  <div>Shifts: {selectedScenario.shifts?.length ?? 0}</div>
                  <div>Demand slots: {totalDemand}</div>
                </div>
              </div>
            )}
          </div>

          {/* Benchmark & Synthetic Dataset Loader */}
          <div className="pt-4 border-t border-border">
            <h3 className="text-base font-semibold text-ink mb-1">Or Load from Benchmark Datasets</h3>
            <p className="text-xs text-ink-muted mb-4">
              Import from the primary Synthetic Manufacturing dataset or external benchmarks (Shift Scheduling, PTSP, Nurse Rostering).
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
              <div>
                <label htmlFor="dataset-select" className="block text-xs font-medium text-ink mb-1">
                  Benchmark Collection:
                </label>
                <select
                  id="dataset-select"
                  value={selectedDatasetId}
                  onChange={e => setSelectedDatasetId(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded bg-surface text-ink text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                >
                  {datasets.map(d => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.name} ({d.total_instances} instances)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="instance-select" className="block text-xs font-medium text-ink mb-1">
                  Instance: {loadingInstances ? '…' : `(${instances.length})`}
                </label>
                <select
                  id="instance-select"
                  value={selectedInstanceId}
                  onChange={e => setSelectedInstanceId(e.target.value)}
                  disabled={loadingInstances || instances.length === 0}
                  className="w-full px-3 py-2 border border-border rounded bg-surface text-ink text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50"
                >
                  {instances.map(inst => (
                    <option key={inst.instance_id} value={inst.instance_id}>
                      {inst.name} — {inst.employee_count} staff, {inst.shift_count} shifts
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-3">
              <button
                type="button"
                onClick={handleLoadBenchmark}
                disabled={loadingBenchmark || loadingInstances || !selectedInstanceId}
                className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
              >
                {loadingBenchmark ? 'Importing Instance…' : 'Import Benchmark Instance'}
              </button>
            </div>

            {/* Benchmark Compatibility Documentation */}
            {loadedInstanceSummary && (
              <div className="mt-4 p-4 bg-surface-muted rounded border border-border text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-ink text-sm">{loadedInstanceSummary.name}</span>
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                    loadedInstanceSummary.compatibility_status === 'COMPATIBLE'
                      ? 'bg-success-soft text-success border border-success'
                      : 'bg-warning-soft text-warning border border-warning'
                  }`}>
                    {loadedInstanceSummary.compatibility_status === 'COMPATIBLE' ? '✓ Fully Compatible' : '≈ Partially Compatible'}
                  </span>
                </div>
                {loadedInstanceSummary.notes && (
                  <p className="text-ink-muted">{loadedInstanceSummary.notes}</p>
                )}
                {loadedInstanceSummary.unsupported_constraints && loadedInstanceSummary.unsupported_constraints.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <p className="font-medium text-warning mb-1">Partially Compatible / Unsupported Constraints in Original Instance:</p>
                    <ul className="list-disc list-inside space-y-0.5 text-ink-muted">
                      {loadedInstanceSummary.unsupported_constraints.map((c, idx) => (
                        <li key={idx}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4 border-t border-border">
            <button
              type="button"
              disabled={!selectedScenarioId || loadingScenario}
              onClick={() => setStep(2)}
              className="px-5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
            >
              Next: Review Workforce →
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Workforce Review */}
      {step === 2 && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-ink">Step 2 — Workforce & Availability Review</h2>
            <p className="text-sm text-ink-muted mt-1">
              Review registered employees and their assigned qualifications and shift availability for this run.
            </p>
          </div>

          <DataTable<Employee>
            columns={employeeColumns}
            data={selectedScenario?.employees || []}
            keyField="id"
            emptyMessage="No employees defined in this scenario."
          />

          <div className="flex justify-between pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors"
            >
              ← Back to Scenario
            </button>
            <button
              type="button"
              onClick={() => setStep(3)}
              className="px-5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
            >
              Next: Unit Demand →
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Unit Demand Matrix */}
      {step === 3 && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-ink">Step 3 — Station Demand Matrix</h2>
            <p className="text-sm text-ink-muted mt-1">
              Required headcount matrix by production unit and operating shift.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-surface-muted">
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-ink-muted uppercase border-b border-border">
                    Production Unit
                  </th>
                  {selectedScenario?.shifts?.map(s => (
                    <th key={s.id} scope="col" className="px-4 py-3 text-center text-xs font-medium text-ink-muted uppercase border-b border-border">
                      {s.name} ({s.id})
                    </th>
                  ))}
                  <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-ink-muted uppercase border-b border-border">
                    Total Demand
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedScenario?.units?.map(unit => {
                  let unitTotal = 0;
                  return (
                    <tr key={unit.id} className="border-b border-border hover:bg-surface-muted/30">
                      <td className="px-4 py-3 font-medium text-ink">
                        {unit.name} <span className="font-mono text-xs text-ink-muted font-normal">({unit.id})</span>
                      </td>
                      {selectedScenario?.shifts?.map(shift => {
                        const d = selectedScenario.demands?.find(
                          dm => dm.unit_id === unit.id && dm.shift_id === shift.id
                        );
                        const count = d?.required_headcount ?? 0;
                        unitTotal += count;
                        return (
                          <td key={shift.id} className="px-4 py-3 text-center font-mono">
                            {count > 0 ? (
                              <span className="px-2.5 py-1 bg-surface-muted rounded font-semibold text-ink">
                                {count}
                              </span>
                            ) : (
                              <span className="text-ink-muted">—</span>
                            )}
                          </td>
                        );
                      })}
                      <td className="px-4 py-3 text-right font-mono font-semibold text-ink">
                        {unitTotal}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-surface-muted font-semibold text-ink">
                  <td className="px-4 py-3">Total Required Positions</td>
                  {selectedScenario?.shifts?.map(shift => {
                    const shiftTotal = selectedScenario.demands
                      ?.filter(dm => dm.shift_id === shift.id)
                      .reduce((acc, curr) => acc + curr.required_headcount, 0) || 0;
                    return (
                      <td key={shift.id} className="px-4 py-3 text-center font-mono">
                        {shiftTotal}
                      </td>
                    );
                  })}
                  <td className="px-4 py-3 text-right font-mono text-primary">
                    {totalDemand}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="flex justify-between pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors"
            >
              ← Back to Workforce
            </button>
            <button
              type="button"
              onClick={() => setStep(4)}
              className="px-5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
            >
              Next: Algorithm & Objective →
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Algorithm & Objective */}
      {step === 4 && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-ink">Step 4 — Algorithm & Objective Setup</h2>
            <p className="text-sm text-ink-muted mt-1">
              Select solver strategy, primary optimization target, and execution limits.
            </p>
          </div>

          <div className="space-y-6 max-w-xl">
            {/* Algorithm Selector */}
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-ink">Solver Algorithm:</legend>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 p-3 border border-border rounded cursor-pointer hover:bg-surface-muted/50 flex-1">
                  <input
                    type="radio"
                    name="algorithm"
                    value="milp"
                    checked={algorithm === 'milp'}
                    onChange={() => setAlgorithm('milp')}
                    className="accent-primary"
                  />
                  <div>
                    <span className="font-semibold text-sm text-ink">MILP (Mathematical Solver)</span>
                    <p className="text-xs text-ink-muted">Rigorous optimization; proves mathematical optimality.</p>
                  </div>
                </label>
                <label className="flex items-center gap-2 p-3 border border-border rounded cursor-pointer hover:bg-surface-muted/50 flex-1">
                  <input
                    type="radio"
                    name="algorithm"
                    value="greedy"
                    checked={algorithm === 'greedy'}
                    onChange={() => setAlgorithm('greedy')}
                    className="accent-primary"
                  />
                  <div>
                    <span className="font-semibold text-sm text-ink">Greedy Baseline</span>
                    <p className="text-xs text-ink-muted">Fast heuristic baseline for comparison; no optimality proof.</p>
                  </div>
                </label>
              </div>
            </fieldset>

            {/* Objective Primary Dropdown */}
            <div>
              <label htmlFor="objective-primary" className="block text-sm font-semibold text-ink mb-1">
                Primary Objective:
              </label>
              <select
                id="objective-primary"
                value={objective.primary}
                onChange={e => setObjective({ ...objective, primary: e.target.value as ObjectiveConfig['primary'] })}
                className="w-full px-3 py-2 border border-border rounded bg-surface text-ink text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              >
                <option value="feasibility">Feasibility (maximize coverage, fulfill hard constraints)</option>
                <option value="cost">Cost Minimisation</option>
                <option value="fairness">Fairness (balance workload)</option>
              </select>
              <p className="text-xs text-ink-muted mt-1.5 bg-surface-muted p-2.5 rounded border border-border">
                Note: Cost minimisation requires cost data configured in the scenario. Fairness objective not yet implemented.
              </p>
            </div>

            {/* Time Limit Input */}
            <div>
              <label htmlFor="time-limit" className="block text-sm font-semibold text-ink mb-1">
                Time Limit (Seconds, 10–300):
              </label>
              <input
                id="time-limit"
                type="number"
                min={10}
                max={300}
                value={timeLimitSeconds}
                onChange={e => setTimeLimitSeconds(Math.max(10, Math.min(300, parseInt(e.target.value, 10) || 60)))}
                className="w-32 px-3 py-2 border border-border rounded bg-surface text-ink text-sm font-mono focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              />
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => setStep(3)}
              className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors"
            >
              ← Back to Demand
            </button>
            <button
              type="button"
              onClick={handleNextFromStep4}
              className="px-5 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
            >
              Next: Validate & Review →
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Validate & Review */}
      {step === 5 && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-ink">Step 5 — Pre-Solve Validation & Input Review</h2>
            <p className="text-sm text-ink-muted mt-1">
              Verify constraints, qualifications, and demand completeness before dispatching to solver.
            </p>
          </div>

          {/* Scenario Summary Card */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-surface-muted rounded-lg border border-border">
            <div>
              <span className="text-xs font-medium text-ink-muted uppercase">Employees</span>
              <p className="text-xl font-mono font-semibold text-ink">{selectedScenario?.employees?.length ?? 0}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-ink-muted uppercase">Production Units</span>
              <p className="text-xl font-mono font-semibold text-ink">{selectedScenario?.units?.length ?? 0}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-ink-muted uppercase">Shifts</span>
              <p className="text-xl font-mono font-semibold text-ink">{selectedScenario?.shifts?.length ?? 0}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-ink-muted uppercase">Total Required Positions</span>
              <p className="text-xl font-mono font-semibold text-ink">{totalDemand}</p>
            </div>
          </div>

          {/* Validation Result Panel */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-ink">Constraint Validation:</h3>
              <button
                type="button"
                onClick={() => selectedScenarioId && runValidation(selectedScenarioId)}
                disabled={isValidating}
                className="text-xs text-primary hover:underline"
              >
                {isValidating ? 'Re-validating…' : 'Re-run check'}
              </button>
            </div>

            {isValidating ? (
              <LoadingSpinner label="Validating input scenario constraints…" />
            ) : (
              <ValidationPanel violations={violations} />
            )}
          </div>

          {/* Execution Plan details */}
          <div className="p-4 bg-surface border border-border rounded text-sm space-y-1">
            <span className="font-semibold text-ink">Optimization Plan:</span>
            <p className="text-ink-muted">
              Solver: <span className="font-mono font-semibold uppercase text-ink">{algorithm}</span> | Objective:{' '}
              <span className="font-mono text-ink">{objective.primary}</span> | Wall limit: {timeLimitSeconds}s
            </p>
          </div>

          <div className="flex justify-between pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => setStep(4)}
              className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors"
            >
              ← Back to Algorithm
            </button>
            <button
              type="button"
              disabled={isValidating || (validationResult !== null && validationResult.errors.length > 0)}
              onClick={handleRunSchedule}
              className="px-6 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              Run Schedule
            </button>
          </div>
        </div>
      )}

      {/* STEP 6: Running */}
      {step === 6 && (
        <div className="bg-surface border border-border rounded-lg p-8 space-y-6 text-center">
          {isRunning ? (
            <div className="py-8 space-y-4">
              <LoadingSpinner label="Solving schedule — please wait." />
              <h2 className="text-lg font-semibold text-ink">Solving schedule — please wait</h2>
              <p className="text-sm text-ink-muted max-w-md mx-auto">
                Executing {algorithm.toUpperCase()} optimization for scenario &quot;{selectedScenario?.name}&quot; with a maximum {timeLimitSeconds}s time limit.
              </p>
            </div>
          ) : error ? (
            <div className="py-4 space-y-6 text-left">
              <ErrorBanner title="Solver Execution Failed" message={error} />
              <div className="flex justify-start gap-3">
                <button
                  type="button"
                  onClick={() => setStep(5)}
                  className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
                >
                  ← Back to Review
                </button>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
