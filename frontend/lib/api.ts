import type {
  HealthResponse, ScenarioSummary, ScenarioResponse, ScenarioCreate,
  ValidationResponse, SolveRequest, SolveResponse, RunSummary,
  MetricsResponse, Employee, ProductionUnit, Shift,
  DatasetMetadata, InstanceSummary, LoadInstanceResponse,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
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
};
