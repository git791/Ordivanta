export type SolverStatus = 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'NOT_SOLVED' | 'ERROR';
export type Algorithm = 'milp' | 'greedy' | 'alns';
export type ObjectivePrimary = 'feasibility' | 'cost' | 'fairness';

export interface Employee {
  id: string;
  name: string;
  skills: string[];
  available_shifts: string[];
  max_hours: number;
}

export interface ProductionUnit {
  id: string;
  name: string;
  required_skills: string[];
}

export interface Shift {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
}

export interface Demand {
  unit_id: string;
  shift_id: string;
  required_headcount: number;
}

export interface ScenarioCreate {
  id: string;
  name: string;
  employees: Employee[];
  units: ProductionUnit[];
  shifts: Shift[];
  demands: Demand[];
}

export interface ScenarioResponse extends ScenarioCreate {
  created_at: string;
}

export interface ScenarioSummary {
  id: string;
  name: string;
  employee_count: number;
  unit_count: number;
  shift_count: number;
  demand_count: number;
  created_at: string;
}

export interface ValidationIssue {
  code: string;
  message: string;
  field: string | null;
  entity_id: string | null;
  severity: string;
}

export interface ValidationResponse {
  is_valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
}

export interface ObjectiveConfig {
  primary: ObjectivePrimary;
  include_assignment_cost: boolean;
  fairness_weight: number;
  two_stage?: boolean;
  two_stage_tolerance?: number;
}

export interface SolveRequest {
  scenario_id: string;
  algorithm: Algorithm;
  objective: ObjectiveConfig;
  time_limit_seconds: number;
}

export interface Assignment {
  employee_id: string;
  unit_id: string;
  shift_id: string;
  hours: number;
}

export interface Violation {
  code: string;
  message: string;
  severity: string;
  employee_id: string | null;
  unit_id: string | null;
  shift_id: string | null;
}

export interface MetricsResponse {
  coverage_rate: number;
  unfilled_positions: number;
  hard_constraint_violations: number;
  employee_hours: Record<string, number>;
  workload_spread: number | null;
  runtime_seconds: number;
  objective_value: number | null;
  total_required_positions: number;
  total_filled_positions: number;
}

export interface SolveResponse {
  run_id: string;
  scenario_id: string;
  algorithm: Algorithm;
  status: SolverStatus;
  runtime_seconds: number;
  objective_value: number | null;
  assignments: Assignment[];
  metrics: MetricsResponse;
  violations: Violation[];
  warnings: string[];
  created_at: string;
}

export interface RunSummary {
  run_id: string;
  scenario_id: string;
  algorithm: Algorithm;
  status: SolverStatus;
  runtime_seconds: number;
  coverage_rate: number;
  hard_constraint_violations: number;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  solver_available: boolean;
  solver_name: string;
  timestamp: string;
}

export interface ApiError {
  errors: Array<{ code: string; message: string; field?: string; entity_id?: string }>;
}

export type CompatibilityStatus = 'COMPATIBLE' | 'PARTIALLY_COMPATIBLE' | 'UNSUPPORTED';

export interface InstanceSummary {
  instance_id: string;
  dataset_id: string;
  name: string;
  filename: string;
  employee_count: number;
  unit_count: number;
  shift_count: number;
  demand_count: number;
  horizon_days: number | null;
  compatibility_status: CompatibilityStatus;
  supported_constraints: string[];
  unsupported_constraints: string[];
  notes: string;
}

export interface DatasetMetadata {
  dataset_id: string;
  name: string;
  category: string;
  description: string;
  source_folder: string;
  file_format: string;
  total_instances: number;
  compatible_instances: number;
  partially_compatible_instances: number;
  unsupported_instances: number;
  fields_available: string[];
  mapped_constraints: string[];
  unsupported_constraints: string[];
  transformation_notes: string;
}

export interface LoadInstanceResponse {
  scenario: ScenarioResponse;
  instance_summary: InstanceSummary;
  compatibility_status: string;
  notes: string;
}
