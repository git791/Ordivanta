from pydantic import BaseModel
from datetime import datetime
from app.domain.enums import SolverStatus, Algorithm, ObjectivePrimary


class ObjectiveConfig(BaseModel):
    primary: ObjectivePrimary = ObjectivePrimary.FEASIBILITY
    include_assignment_cost: bool = False
    fairness_weight: float = 0.0


class SolveRequest(BaseModel):
    scenario_id: str
    algorithm: Algorithm = Algorithm.MILP
    objective: ObjectiveConfig = ObjectiveConfig()
    time_limit_seconds: int = 60


class AssignmentResponse(BaseModel):
    employee_id: str
    unit_id: str
    shift_id: str
    hours: float


class ViolationResponse(BaseModel):
    code: str
    message: str
    severity: str
    employee_id: str | None = None
    unit_id: str | None = None
    shift_id: str | None = None


class MetricsResponse(BaseModel):
    coverage_rate: float
    unfilled_positions: int
    hard_constraint_violations: int
    employee_hours: dict[str, float]
    workload_spread: float | None
    runtime_seconds: float
    objective_value: float | None
    total_required_positions: int
    total_filled_positions: int


class SolveResponse(BaseModel):
    run_id: str
    scenario_id: str
    algorithm: Algorithm
    status: SolverStatus
    runtime_seconds: float
    objective_value: float | None
    assignments: list[AssignmentResponse]
    metrics: MetricsResponse
    violations: list[ViolationResponse]
    warnings: list[str] = []
    created_at: datetime


class RunSummary(BaseModel):
    run_id: str
    scenario_id: str
    algorithm: Algorithm
    status: SolverStatus
    runtime_seconds: float
    coverage_rate: float
    hard_constraint_violations: int
    created_at: datetime
