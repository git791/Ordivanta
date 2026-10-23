from pydantic import BaseModel
from .employee import EmployeeCreate, EmployeeResponse
from datetime import datetime


class ShiftCreate(BaseModel):
    id: str
    name: str
    start_time: str
    end_time: str
    duration_hours: float


class ShiftResponse(ShiftCreate):
    pass


class UnitCreate(BaseModel):
    id: str
    name: str
    required_skills: list[str] = []


class UnitResponse(UnitCreate):
    pass


class DemandCreate(BaseModel):
    unit_id: str
    shift_id: str
    required_headcount: int


class DemandResponse(DemandCreate):
    pass


class ScenarioCreate(BaseModel):
    id: str
    name: str
    employees: list[EmployeeCreate] = []
    units: list[UnitCreate] = []
    shifts: list[ShiftCreate] = []
    demands: list[DemandCreate] = []


class ScenarioResponse(BaseModel):
    id: str
    name: str
    employees: list[EmployeeResponse]
    units: list[UnitResponse]
    shifts: list[ShiftResponse]
    demands: list[DemandResponse]
    created_at: datetime


class ScenarioSummary(BaseModel):
    id: str
    name: str
    employee_count: int
    unit_count: int
    shift_count: int
    demand_count: int
    created_at: datetime


class ValidationIssue(BaseModel):
    code: str
    message: str
    field: str | None = None
    entity_id: str | None = None
    severity: str


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
