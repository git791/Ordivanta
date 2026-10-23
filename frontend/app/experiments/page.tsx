'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { api } from '@/lib/api';
import type { ScenarioSummary, SolveResponse, SolveRequest, DatasetMetadata, InstanceSummary } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import { ArrowDownTrayIcon, PlayIcon, BeakerIcon } from '@heroicons/react/24/outline';

export default function ExperimentsPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [milpRun, setMilpRun] = useState<SolveResponse | null>(null);
  const [greedyRun, setGreedyRun] = useState<SolveResponse | null>(null);
  const [runningMilp, setRunningMilp] = useState<boolean>(false);
  const [runningGreedy, setRunningGreedy] = useState<boolean>(false);

  // Benchmark Datasets state
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('synthetic_manufacturing');
  const [instances, setInstances] = useState<InstanceSummary[]>([]);
  const [selectedInstanceId, setSelectedInstanceId] = useState<string>('');
  const [loadingInstances, setLoadingInstances] = useState<boolean>(false);
  const [loadingBenchmark, setLoadingBenchmark] = useState<boolean>(false);
  const [loadedInstanceSummary, setLoadedInstanceSummary] = useState<InstanceSummary | null>(null);

  const fetchScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getScenarios();
      setScenarios(data || []);
      if (data && data.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(data[0].id);
      }
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to load scenarios for experiments.');
    } finally {
      setLoading(false);
    }
  }, [selectedScenarioId]);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  // Load datasets on mount
  useEffect(() => {
    api.getDatasets()
      .then(d => setDatasets(d || []))
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

  const handleLoadBenchmark = async () => {
    if (!selectedDatasetId || !selectedInstanceId) return;
    setLoadingBenchmark(true);
    setError(null);
    try {
      const res = await api.loadDatasetInstance(selectedDatasetId, selectedInstanceId);
      await fetchScenarios();
      setSelectedScenarioId(res.scenario.id);
      setMilpRun(null);
      setGreedyRun(null);
      setLoadedInstanceSummary(res.instance_summary);
    } catch (err: unknown) {
      console.error('Failed to load benchmark instance:', err);
      setError('Failed to import benchmark instance.');
    } finally {
      setLoadingBenchmark(false);
    }
  };

  const selectedScenarioName = useMemo(() => {
    return scenarios.find(s => s.id === selectedScenarioId)?.name ?? selectedScenarioId;
  }, [scenarios, selectedScenarioId]);

  const runAlgorithm = async (algo: 'milp' | 'greedy') => {
    if (!selectedScenarioId) return;
    setError(null);
    if (algo === 'milp') setRunningMilp(true);
    else setRunningGreedy(true);

    const payload: SolveRequest = {
      scenario_id: selectedScenarioId,
      algorithm: algo,
      objective: {
        primary: 'feasibility',
        include_assignment_cost: false,
        fairness_weight: 0,
      },
      time_limit_seconds: 60,
    };

    try {
      const res = await api.solve(payload);
      if (algo === 'milp') {
        setMilpRun(res);
      } else {
        setGreedyRun(res);
      }
    } catch (err: unknown) {
      console.error(`Failed to run ${algo}:`, err);
      setError(`Failed to execute ${algo.toUpperCase()} algorithm.`);
    } finally {
      if (algo === 'milp') setRunningMilp(false);
      else setRunningGreedy(false);
    }
  };

  const handleDownloadComparison = () => {
    if (!milpRun && !greedyRun) return;

    const data = {
      scenario_id: selectedScenarioId,
      scenario_name: selectedScenarioName,
      timestamp: new Date().toISOString(),
      comparison: {
        milp: milpRun,
        greedy: greedyRun,
      },
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `experiment-comparison-${selectedScenarioId}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <LoadingSpinner label="Loading experiment environment…" />;
  }

  const bothRan = milpRun !== null && greedyRun !== null;

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Algorithm Experiments & Benchmarks"
        description="Compare exact MILP optimization against the Greedy baseline using identical input scenarios."
      />

      {error && <ErrorBanner title="Execution Error" message={error} />}

      {/* Scenario & Control Bar */}
      <div className="bg-surface border border-border rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex-1 max-w-md">
            <label htmlFor="scenario-selector" className="block text-xs font-semibold text-ink uppercase mb-1">
              Select Benchmark Scenario:
            </label>
            <select
              id="scenario-selector"
              value={selectedScenarioId}
              onChange={e => {
                setSelectedScenarioId(e.target.value);
                setMilpRun(null);
                setGreedyRun(null);
              }}
              className="w-full px-3 py-2 border border-border rounded bg-surface text-ink text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              {scenarios.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.employee_count} emp, {s.unit_count} units, {s.shift_count} shifts)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => runAlgorithm('milp')}
              disabled={runningMilp || !selectedScenarioId}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              <PlayIcon className="w-4 h-4" aria-hidden="true" />
              {runningMilp ? 'Solving MILP…' : 'Run MILP'}
            </button>

            <button
              type="button"
              onClick={() => runAlgorithm('greedy')}
              disabled={runningGreedy || !selectedScenarioId}
              className="inline-flex items-center gap-2 px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              <PlayIcon className="w-4 h-4" aria-hidden="true" />
              {runningGreedy ? 'Running Greedy…' : 'Run Greedy'}
            </button>
          </div>
        </div>

        {/* Benchmark Dataset Import */}
        <div className="pt-4 border-t border-border">
          <p className="text-xs font-semibold text-ink uppercase mb-2">Import from Benchmark Datasets:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <select
                aria-label="Benchmark Collection"
                value={selectedDatasetId}
                onChange={e => setSelectedDatasetId(e.target.value)}
                className="w-full px-3 py-1.5 border border-border rounded bg-surface text-ink text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              >
                {datasets.map(d => (
                  <option key={d.dataset_id} value={d.dataset_id}>
                    {d.name} ({d.total_instances})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <select
                aria-label="Instance Selection"
                value={selectedInstanceId}
                onChange={e => setSelectedInstanceId(e.target.value)}
                disabled={loadingInstances || instances.length === 0}
                className="w-full px-3 py-1.5 border border-border rounded bg-surface text-ink text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50"
              >
                {instances.map(inst => (
                  <option key={inst.instance_id} value={inst.instance_id}>
                    {inst.name} — {inst.employee_count} staff, {inst.shift_count} shifts
                  </option>
                ))}
              </select>
            </div>
            <div>
              <button
                type="button"
                onClick={handleLoadBenchmark}
                disabled={loadingBenchmark || loadingInstances || !selectedInstanceId}
                className="w-full sm:w-auto px-4 py-1.5 bg-surface border border-border rounded text-xs font-medium text-ink hover:bg-surface-muted transition-colors disabled:opacity-50"
              >
                {loadingBenchmark ? 'Importing…' : 'Import Instance'}
              </button>
            </div>
          </div>

          {loadedInstanceSummary && (
            <div className="mt-3 p-3 bg-surface-muted rounded border border-border text-xs flex items-center justify-between">
              <div>
                <span className="font-semibold text-ink">{loadedInstanceSummary.name}</span>
                <span className="text-ink-muted ml-2">({loadedInstanceSummary.employee_count} staff, {loadedInstanceSummary.shift_count} shifts)</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                loadedInstanceSummary.compatibility_status === 'COMPATIBLE'
                  ? 'bg-success-soft text-success border border-success'
                  : 'bg-warning-soft text-warning border border-warning'
              }`}>
                {loadedInstanceSummary.compatibility_status === 'COMPATIBLE' ? '✓ Fully Compatible' : '≈ Partially Compatible'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Section */}
      {bothRan && (
        <div className="p-3.5 bg-primary-soft/50 border border-primary/30 rounded-lg text-sm text-ink flex items-center justify-between">
          <span>
            Both algorithms used the same scenario: <strong>{selectedScenarioName}</strong>.
          </span>
          <button
            type="button"
            onClick={handleDownloadComparison}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-border rounded text-xs font-medium text-ink hover:bg-surface-muted transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          >
            <ArrowDownTrayIcon className="w-3.5 h-3.5" aria-hidden="true" />
            Download Comparison (JSON)
          </button>
        </div>
      )}

      {/* Comparison Table */}
      {(milpRun || greedyRun) && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="p-4 border-b border-border bg-surface-muted/50">
            <h2 className="text-base font-semibold text-ink">Benchmark Results Comparison</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-surface-muted">
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-ink-muted uppercase border-b border-border">
                    Metric
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-ink-muted uppercase border-b border-border">
                    MILP (Exact Solver)
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-ink-muted uppercase border-b border-border">
                    Greedy (Baseline Heuristic)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {/* Status */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Solver Status</td>
                  <td className="px-4 py-3">
                    {milpRun ? <StatusBadge status={milpRun.status} size="sm" /> : <span className="text-ink-muted italic">Not run yet</span>}
                  </td>
                  <td className="px-4 py-3">
                    {greedyRun ? <StatusBadge status={greedyRun.status} size="sm" /> : <span className="text-ink-muted italic">Not run yet</span>}
                  </td>
                </tr>

                {/* Coverage */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Coverage Rate</td>
                  <td className="px-4 py-3 font-mono">
                    {milpRun ? (
                      <span className="font-semibold text-primary">
                        {(milpRun.metrics.coverage_rate * 100).toFixed(1)}% ({milpRun.metrics.total_filled_positions} / {milpRun.metrics.total_required_positions})
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {greedyRun ? (
                      <span>
                        {(greedyRun.metrics.coverage_rate * 100).toFixed(1)}% ({greedyRun.metrics.total_filled_positions} / {greedyRun.metrics.total_required_positions})
                      </span>
                    ) : '—'}
                  </td>
                </tr>

                {/* Violations */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Violations</td>
                  <td className="px-4 py-3 font-mono">
                    {milpRun ? (
                      <span className={milpRun.violations.length > 0 ? 'text-danger font-semibold' : 'text-success'}>
                        {milpRun.violations.length}
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {greedyRun ? (
                      <span className={greedyRun.violations.length > 0 ? 'text-danger font-semibold' : 'text-success'}>
                        {greedyRun.violations.length}
                      </span>
                    ) : '—'}
                  </td>
                </tr>

                {/* Runtime */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Runtime (Wall Clock)</td>
                  <td className="px-4 py-3 font-mono">
                    {milpRun ? `${milpRun.runtime_seconds.toFixed(3)}s` : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {greedyRun ? `${greedyRun.runtime_seconds.toFixed(3)}s` : '—'}
                  </td>
                </tr>

                {/* Objective */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Objective Value</td>
                  <td className="px-4 py-3 font-mono">
                    {milpRun && milpRun.objective_value !== null ? milpRun.objective_value.toFixed(2) : 'N/A'}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {greedyRun && greedyRun.objective_value !== null ? greedyRun.objective_value.toFixed(2) : 'N/A'}
                  </td>
                </tr>

                {/* Unfilled positions */}
                <tr>
                  <td className="px-4 py-3 font-medium text-ink">Unfilled Positions</td>
                  <td className="px-4 py-3 font-mono">
                    {milpRun ? milpRun.metrics.unfilled_positions : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {greedyRun ? greedyRun.metrics.unfilled_positions : '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State before running */}
      {!milpRun && !greedyRun && !runningMilp && !runningGreedy && (
        <div className="bg-surface border border-border rounded-lg p-8 text-center">
          <BeakerIcon className="w-10 h-10 text-steel mx-auto mb-3" aria-hidden="true" />
          <h3 className="text-base font-semibold text-ink">No benchmark executed yet</h3>
          <p className="text-sm text-ink-muted mt-1 max-w-md mx-auto">
            Choose a benchmark scenario above and click &quot;Run MILP&quot; and &quot;Run Greedy&quot; to execute comparative performance experiments.
          </p>
        </div>
      )}

      {/* Methodology Note */}
      <div className="bg-surface-muted border border-border rounded-lg p-4 text-xs text-ink-muted space-y-1">
        <p className="font-semibold text-ink">Scientific Methodology Note:</p>
        <p>
          Greedy never proves optimality. OPTIMAL status for MILP means the solver has proven the solution optimal. Compare results on identical scenarios.
        </p>
      </div>
    </div>
  );
}
