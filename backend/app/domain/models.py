from dataclasses import dataclass, field
from datetime import datetime
from .enums import SolverStatus, Algorithm


@dataclass
class SkillRequirement:
    """Represents a skill requirement with an optional minimum proficiency level."""
    skill: str
    min_level: int = 1  # 1–5 scale; 1 means any proficiency is accepted


@dataclass
class Employee:
    id: str
    name: str
    skills: list[str]
    available_shifts: list[str]  # shift IDs
    max_hours: float

    # --- Phase 2/3: Extended qualification fields ---
    # Proficiency levels keyed by skill name (1=novice … 5=expert).
    # Absent implies level 1 for any skill listed in `skills`.
    skill_levels: dict[str, int] = field(default_factory=dict)
    # Certifications held by the employee (e.g. "forklift_license", "first_aid").
    certifications: list[str] = field(default_factory=list)

    # --- Phase 2: Absenteeism ---
    # When True, the employee is absent for the entire planning horizon.
    # Schedulers must not assign absent employees.
    is_absent: bool = False
    # Absence reason tag (informational only; not used in optimisation).
    absence_reason: str | None = None

    # --- Phase 4: Overtime and on-call ---
    # Whether the employee has voluntarily opted in to work overtime.
    # Overtime is ONLY permitted when this is True AND hour limits allow it.
    overtime_opt_in: bool = False
    # Regular (non-overtime) scheduled hours limit.
    # If None, falls back to max_hours (backward-compatible).
    regular_hours_limit: float | None = None
    # Maximum overtime hours permitted on top of regular_hours_limit (when opted in).
    max_overtime_hours: float = 0.0
    # Overtime hourly premium paid on top of base_hourly_rate (not a replacement).
    # E.g. base=20, premium=10 means OT hours cost 30/h.
    overtime_hourly_premium: float = 0.0
    # Base hourly pay rate for regular hours.
    base_hourly_rate: float = 0.0
    # Shift IDs for which this employee is available on an on-call (call-in) basis.
    # Only confirmed call-in assignments are valid; unconfirmed on-call ≠ available.
    on_call_shifts: list[str] = field(default_factory=list)
    # Minimum notice required (hours) before a call-in assignment can be confirmed.
    call_in_lead_hours: float = 0.0
    # Shift preferences: positive = preferred, negative = disliked.
    shift_preferences: dict[str, int] = field(default_factory=dict)

    def effective_max_hours(self) -> float:
        """
        Return the maximum hours this employee may be scheduled.
        If overtime is opted in, includes overtime budget on top of regular limit.
        """
        base = self.regular_hours_limit if self.regular_hours_limit is not None else self.max_hours
        if self.overtime_opt_in:
            return base + self.max_overtime_hours
        return base


@dataclass
class ProductionUnit:
    id: str
    name: str
    required_skills: list[str]

    # --- Phase 3: Structured skill requirements (used by ALL / LEVEL_AND_CERTIFICATION) ---
    # When non-empty, each entry specifies a skill + minimum proficiency required.
    # Falls back to required_skills list when empty (backward-compatible).
    mandatory_skill_requirements: list[SkillRequirement] = field(default_factory=list)
    # Certifications that assigned employees must hold (for LEVEL_AND_CERTIFICATION policy).
    required_certifications: list[str] = field(default_factory=list)


@dataclass
class Shift:
    id: str
    name: str
    start_time: str   # "HH:MM" or ISO datetime
    end_time: str     # "HH:MM" or ISO datetime
    duration_hours: float


@dataclass
class Demand:
    unit_id: str
    shift_id: str
    required_headcount: int
    # Whether this demand cell represents a safety-critical / critical position.
    is_critical: bool = False


@dataclass
class ScenarioGenerationParams:
    """Records how a scenario was generated for full reproducibility."""
    seed: int
    num_employees: int
    num_units: int
    horizon_days: int
    headcount_per_cell: int
    max_hours_per_week: float
    absenteeism_rate: float = 0.0
    demand_multiplier: float = 1.0
    overtime_enabled: bool = False
    strict_qualifications: bool = False
    min_rest_hours: float = 0.0
    qualification_policy: str = "ANY"


@dataclass
class Scenario:
    id: str
    name: str
    employees: list[Employee] = field(default_factory=list)
    units: list[ProductionUnit] = field(default_factory=list)
    shifts: list[Shift] = field(default_factory=list)
    demands: list[Demand] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    # Generation parameters (populated only for generated scenarios).
    generation_params: ScenarioGenerationParams | None = None


@dataclass
class Assignment:
    employee_id: str
    unit_id: str
    shift_id: str
    hours: float
    # Whether this assignment is locked (cannot be changed in rescheduling).
    is_locked: bool = False
    # Whether this is an overtime assignment (hours beyond regular_hours_limit).
    is_overtime: bool = False


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
