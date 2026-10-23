from dataclasses import dataclass, field
from datetime import datetime
from .enums import SolverStatus, Algorithm


@dataclass
class Employee:
    id: str
    name: str
    skills: list[str]
    available_shifts: list[str]  # shift IDs
    max_hours: float


@dataclass
class ProductionUnit:
    id: str
    name: str
    required_skills: list[str]


@dataclass
class Shift:
    id: str
    name: str
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"
    duration_hours: float


@dataclass
class Demand:
    unit_id: str
    shift_id: str
    required_headcount: int


@dataclass
class Scenario:
    id: str
    name: str
    employees: list[Employee] = field(default_factory=list)
    units: list[ProductionUnit] = field(default_factory=list)
    shifts: list[Shift] = field(default_factory=list)
    demands: list[Demand] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Assignment:
    employee_id: str
    unit_id: str
    shift_id: str
    hours: float


@dataclass
class ScheduleRun:
    run_id: str
    scenario_id: str
    algorithm: Algorithm
    status: SolverStatus
    runtime_seconds: float
    objective_value: float | None
    assignments: list[Assignment]
    warnings: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ValidationError:
    code: str
    message: str
    field: str | None = None
    entity_id: str | None = None
    severity: str = "error"  # "error" | "warning"
    employee_id: str | None = None
    unit_id: str | None = None
    shift_id: str | None = None


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
