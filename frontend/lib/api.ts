import type {
  HealthResponse, ScenarioSummary, ScenarioResponse, ScenarioCreate,
  ValidationResponse, SolveRequest, SolveResponse, RunSummary,
  MetricsResponse, Employee, ProductionUnit, Shift,
  DatasetMetadata, InstanceSummary, LoadInstanceResponse,
} from './types';

const rawBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
export const BASE = rawBase.trim().replace(/\/+$/, '');

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${BASE}${cleanPath}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  const body = await res.json();
  if (!res.ok) throw body;
  return body;
}

export const api = {
  health: () => apiFetch<HealthResponse>('/api/health'),
  
  getScenarios: () => apiFetch<ScenarioSummary[]>('/api/scenarios'),
  getScenario: (id: string) => apiFetch<ScenarioResponse>(`/api/scenarios/${id}`),
  createScenario: (body: ScenarioCreate) =>
    apiFetch<ScenarioResponse>('/api/scenarios', { method: 'POST', body: JSON.stringify(body) }),
  validateScenario: (id: string) =>
    apiFetch<ValidationResponse>(`/api/scenarios/${id}/validate`, { method: 'POST' }),
  loadSample: () =>
    apiFetch<ScenarioResponse>('/api/scenarios/sample', { method: 'POST' }),
  deleteScenario: (id: string) =>
    apiFetch<void>(`/api/scenarios/${id}`, { method: 'DELETE' }),
  
  solve: (body: SolveRequest) =>
    apiFetch<SolveResponse>('/api/schedules/solve', { method: 'POST', body: JSON.stringify(body) }),
  getRuns: () => apiFetch<RunSummary[]>('/api/schedules'),
  getRun: (runId: string) => apiFetch<SolveResponse>(`/api/schedules/${runId}`),
  getMetrics: (runId: string) => apiFetch<MetricsResponse>(`/api/schedules/${runId}/metrics`),
  exportCsvUrl: (runId: string) => `${BASE}/api/schedules/${runId}/export`,
  
  getEmployees: () => apiFetch<Employee[]>('/api/employees'),
  getUnits: () => apiFetch<ProductionUnit[]>('/api/units'),
  getShifts: () => apiFetch<Shift[]>('/api/shifts'),

  getDatasets: () => apiFetch<DatasetMetadata[]>('/api/datasets'),
  getDataset: (datasetId: string) => apiFetch<DatasetMetadata>(`/api/datasets/${datasetId}`),
  getDatasetInstances: (datasetId: string) =>
    apiFetch<InstanceSummary[]>(`/api/datasets/${datasetId}/instances`),
  getInstanceDetails: (datasetId: string, instanceId: string) =>
    apiFetch<InstanceSummary>(`/api/datasets/${datasetId}/instances/${instanceId}`),
  loadDatasetInstance: (datasetId: string, instanceId: string) =>
    apiFetch<LoadInstanceResponse>(`/api/datasets/${datasetId}/load/${instanceId}`, { method: 'POST' }),

  getDatasetManifest: () => apiFetch<any>('/api/datasets/manifest'),
  getTaskBenchmarks: (datasetId?: string) =>
    apiFetch<Record<string, any[]>>(`/api/tasks/benchmarks${datasetId ? `?dataset_id=${datasetId}` : ''}`),
  getTaskInstance: (datasetId: string, instanceId: string, maxTasks?: number) =>
    apiFetch<any>(`/api/tasks/instance/${datasetId}/${instanceId}${maxTasks ? `?max_tasks=${maxTasks}` : ''}`),
  solveTaskAllocation: (body: { dataset_id: string; instance_id: string; algorithm: string; max_tasks?: number; time_limit?: number }) =>
    apiFetch<any>('/api/tasks/solve', { method: 'POST', body: JSON.stringify(body) }),
  bridgeWorkflow: (body: { facility_id?: string; shift_name?: string; task_count?: number }) =>
    apiFetch<any>('/api/tasks/workflow/bridge', { method: 'POST', body: JSON.stringify(body) }),

  startLargeScaleBenchmark: (body: { workers: number; tasks: number; algorithm: string; time_limit: number; seed?: number }) =>
    apiFetch<any>('/api/tasks/large-scale/start', { method: 'POST', body: JSON.stringify(body) }),
  getLargeScaleJobStatus: (jobId: string) =>
    apiFetch<any>(`/api/tasks/large-scale/jobs/${jobId}`),
  cancelLargeScaleJob: (jobId: string) =>
    apiFetch<any>(`/api/tasks/large-scale/jobs/${jobId}/cancel`, { method: 'POST' }),
  exportLargeScaleJobUrl: (jobId: string, format: string = 'csv') =>
    `${BASE}/api/tasks/large-scale/jobs/${jobId}/export?format=${format}`,
};
