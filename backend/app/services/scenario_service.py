from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioSummary,
    ValidationIssue,
    ValidationResponse,
    ShiftResponse,
    UnitResponse,
    DemandResponse,
)
from app.schemas.employee import EmployeeResponse
from app.validation.input_validator import validate_scenario
from app.sample_data import get_sample_scenario
from app.persistence import repository


class ScenarioNotFoundError(Exception):
    pass


class ValidationFailedError(Exception):
    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


def domain_to_response(scenario: Scenario) -> ScenarioResponse:
    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        employees=[
            EmployeeResponse(
                id=e.id,
                name=e.name,
                skills=e.skills,
                available_shifts=e.available_shifts,
                max_hours=e.max_hours,
            )
            for e in scenario.employees
        ],
        units=[
            UnitResponse(
                id=u.id,
                name=u.name,
                required_skills=u.required_skills,
            )
            for u in scenario.units
        ],
        shifts=[
            ShiftResponse(
                id=s.id,
                name=s.name,
                start_time=s.start_time,
                end_time=s.end_time,
                duration_hours=s.duration_hours,
            )
            for s in scenario.shifts
        ],
        demands=[
            DemandResponse(
                unit_id=d.unit_id,
                shift_id=d.shift_id,
                required_headcount=d.required_headcount,
            )
            for d in scenario.demands
        ],
        created_at=scenario.created_at,
    )


async def create_scenario(
    session: AsyncSession, data: ScenarioCreate
) -> ScenarioResponse:
    scenario = Scenario(
        id=data.id,
        name=data.name,
        employees=[
            Employee(
                id=e.id,
                name=e.name,
                skills=e.skills,
                available_shifts=e.available_shifts,
                max_hours=e.max_hours,
            )
            for e in data.employees
        ],
        units=[
            ProductionUnit(
                id=u.id,
                name=u.name,
                required_skills=u.required_skills,
            )
            for u in data.units
        ],
        shifts=[
            Shift(
                id=s.id,
                name=s.name,
                start_time=s.start_time,
                end_time=s.end_time,
                duration_hours=s.duration_hours,
            )
            for s in data.shifts
        ],
        demands=[
            Demand(
                unit_id=d.unit_id,
                shift_id=d.shift_id,
                required_headcount=d.required_headcount,
            )
            for d in data.demands
        ],
        created_at=datetime.utcnow(),
    )
    await repository.save_scenario(session, scenario)
    return domain_to_response(scenario)


async def get_scenario_domain(session: AsyncSession, id: str) -> Scenario:
    scenario = await repository.get_scenario(session, id)
    if not scenario:
        raise ScenarioNotFoundError(f"Scenario '{id}' not found")
    return scenario


async def get_scenario(session: AsyncSession, id: str) -> ScenarioResponse:
    scenario = await get_scenario_domain(session, id)
    return domain_to_response(scenario)


async def delete_scenario(session: AsyncSession, id: str) -> None:
    deleted = await repository.delete_scenario(session, id)
    if not deleted:
        raise ScenarioNotFoundError(f"Scenario '{id}' not found")


async def list_scenarios(session: AsyncSession) -> list[ScenarioSummary]:
    return await repository.list_scenarios(session)


async def validate_scenario_by_id(
    session: AsyncSession, id: str
) -> ValidationResponse:
    scenario = await get_scenario_domain(session, id)
    val_result = validate_scenario(scenario)
    return ValidationResponse(
        is_valid=val_result.is_valid,
        errors=[
            ValidationIssue(
                code=e.code,
                message=e.message,
                field=e.field,
                entity_id=e.entity_id,
                severity=e.severity,
            )
            for e in val_result.errors
        ],
        warnings=[
            ValidationIssue(
                code=w.code,
                message=w.message,
                field=w.field,
                entity_id=w.entity_id,
                severity=w.severity,
            )
            for w in val_result.warnings
        ],
    )


async def load_sample_scenario(session: AsyncSession) -> ScenarioResponse:
    scenario = get_sample_scenario()
    await repository.save_scenario(session, scenario)
    return domain_to_response(scenario)
