import json
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Text, Integer, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Base
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.schemas.scenario import ScenarioSummary
from app.schemas.schedule import SolveResponse, RunSummary
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.schemas.scenario import UnitCreate, UnitResponse, ShiftCreate, ShiftResponse


class ScenarioORM(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)


class ScheduleRunORM(Base):
    __tablename__ = "schedule_runs"
    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    runtime_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    objective_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_rate: Mapped[float] = mapped_column(Float, default=0.0)
    hard_constraint_violations: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)


class EmployeeORM(Base):
    __tablename__ = "employees"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    available_shifts_json: Mapped[str] = mapped_column(Text, default="[]")
    max_hours: Mapped[float] = mapped_column(Float, nullable=False)


class UnitORM(Base):
    __tablename__ = "units"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]")


class ShiftORM(Base):
    __tablename__ = "shifts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[str] = mapped_column(String, nullable=False)
    end_time: Mapped[str] = mapped_column(String, nullable=False)
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)


def scenario_to_json(s: Scenario) -> str:
    d = {
        "id": s.id,
        "name": s.name,
        "employees": [
            {
                "id": e.id,
                "name": e.name,
                "skills": e.skills,
                "available_shifts": e.available_shifts,
                "max_hours": e.max_hours,
            }
            for e in s.employees
        ],
        "units": [
            {
                "id": u.id,
                "name": u.name,
                "required_skills": u.required_skills,
            }
            for u in s.units
        ],
        "shifts": [
            {
                "id": sh.id,
                "name": sh.name,
                "start_time": sh.start_time,
                "end_time": sh.end_time,
                "duration_hours": sh.duration_hours,
            }
            for sh in s.shifts
        ],
        "demands": [
            {
                "unit_id": dm.unit_id,
                "shift_id": dm.shift_id,
                "required_headcount": dm.required_headcount,
            }
            for dm in s.demands
        ],
        "created_at": s.created_at.isoformat() if s.created_at else datetime.utcnow().isoformat(),
    }
    return json.dumps(d)


def json_to_scenario(json_str: str) -> Scenario:
    d = json.loads(json_str)
    created_at = datetime.utcnow()
    if "created_at" in d and d["created_at"]:
        try:
            created_at = datetime.fromisoformat(d["created_at"])
        except ValueError:
            pass

    return Scenario(
        id=d["id"],
        name=d["name"],
        employees=[
            Employee(
                id=e["id"],
                name=e["name"],
                skills=e.get("skills", []),
                available_shifts=e.get("available_shifts", []),
                max_hours=float(e["max_hours"]),
            )
            for e in d.get("employees", [])
        ],
        units=[
            ProductionUnit(
                id=u["id"],
                name=u["name"],
                required_skills=u.get("required_skills", []),
            )
            for u in d.get("units", [])
        ],
        shifts=[
            Shift(
                id=sh["id"],
                name=sh["name"],
                start_time=sh["start_time"],
                end_time=sh["end_time"],
                duration_hours=float(sh["duration_hours"]),
            )
            for sh in d.get("shifts", [])
        ],
        demands=[
            Demand(
                unit_id=dm["unit_id"],
                shift_id=dm["shift_id"],
                required_headcount=int(dm["required_headcount"]),
            )
            for dm in d.get("demands", [])
        ],
        created_at=created_at,
    )


# Scenario CRUD
async def save_scenario(session: AsyncSession, scenario: Scenario) -> str:
    input_json = scenario_to_json(scenario)
    obj = await session.get(ScenarioORM, scenario.id)
    if obj:
        obj.name = scenario.name
        obj.input_json = input_json
    else:
        obj = ScenarioORM(
            id=scenario.id,
            name=scenario.name,
            created_at=scenario.created_at,
            input_json=input_json,
        )
        session.add(obj)
    await session.commit()
    return scenario.id


async def get_scenario(session: AsyncSession, id: str) -> Scenario | None:
    obj = await session.get(ScenarioORM, id)
    if not obj:
        return None
    return json_to_scenario(obj.input_json)


async def delete_scenario(session: AsyncSession, id: str) -> bool:
    obj = await session.get(ScenarioORM, id)
    if not obj:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def list_scenarios(session: AsyncSession) -> list[ScenarioSummary]:
    stmt = select(ScenarioORM).order_by(ScenarioORM.created_at.desc())
    res = await session.execute(stmt)
    records = res.scalars().all()
    summaries = []
    for r in records:
        try:
            d = json.loads(r.input_json)
            summaries.append(
                ScenarioSummary(
                    id=r.id,
                    name=r.name,
                    employee_count=len(d.get("employees", [])),
                    unit_count=len(d.get("units", [])),
                    shift_count=len(d.get("shifts", [])),
                    demand_count=len(d.get("demands", [])),
                    created_at=r.created_at,
                )
            )
        except Exception:
            summaries.append(
                ScenarioSummary(
                    id=r.id,
                    name=r.name,
                    employee_count=0,
                    unit_count=0,
                    shift_count=0,
                    demand_count=0,
                    created_at=r.created_at,
                )
            )
    return summaries


# Schedule Run CRUD
async def save_run(session: AsyncSession, run_data: SolveResponse) -> str:
    result_json = run_data.model_dump_json()
    obj = await session.get(ScheduleRunORM, run_data.run_id)
    if obj:
        obj.result_json = result_json
        obj.status = run_data.status.value
        obj.runtime_seconds = run_data.runtime_seconds
        obj.objective_value = run_data.objective_value
        obj.coverage_rate = run_data.metrics.coverage_rate
        obj.hard_constraint_violations = run_data.metrics.hard_constraint_violations
    else:
        obj = ScheduleRunORM(
            run_id=run_data.run_id,
            scenario_id=run_data.scenario_id,
            algorithm=run_data.algorithm.value,
            status=run_data.status.value,
            runtime_seconds=run_data.runtime_seconds,
            objective_value=run_data.objective_value,
            coverage_rate=run_data.metrics.coverage_rate,
            hard_constraint_violations=run_data.metrics.hard_constraint_violations,
            created_at=run_data.created_at,
            result_json=result_json,
        )
        session.add(obj)
    await session.commit()
    return run_data.run_id


async def get_run(session: AsyncSession, run_id: str) -> SolveResponse | None:
    obj = await session.get(ScheduleRunORM, run_id)
    if not obj:
        return None
    return SolveResponse.model_validate_json(obj.result_json)


async def list_runs(
    session: AsyncSession, scenario_id: str | None = None
) -> list[RunSummary]:
    stmt = select(ScheduleRunORM)
    if scenario_id:
        stmt = stmt.where(ScheduleRunORM.scenario_id == scenario_id)
    stmt = stmt.order_by(ScheduleRunORM.created_at.desc())
    res = await session.execute(stmt)
    records = res.scalars().all()
    summaries = []
    for r in records:
        summaries.append(
            RunSummary(
                run_id=r.run_id,
                scenario_id=r.scenario_id,
                algorithm=r.algorithm,
                status=r.status,
                runtime_seconds=r.runtime_seconds,
                coverage_rate=r.coverage_rate,
                hard_constraint_violations=r.hard_constraint_violations,
                created_at=r.created_at,
            )
        )
    return summaries


# Standalone Workforce CRUD (Union with Scenarios for GET)
async def save_employee(session: AsyncSession, emp: EmployeeCreate) -> EmployeeResponse:
    obj = await session.get(EmployeeORM, emp.id)
    if obj:
        obj.name = emp.name
        obj.skills_json = json.dumps(emp.skills)
        obj.available_shifts_json = json.dumps(emp.available_shifts)
        obj.max_hours = emp.max_hours
    else:
        obj = EmployeeORM(
            id=emp.id,
            name=emp.name,
            skills_json=json.dumps(emp.skills),
            available_shifts_json=json.dumps(emp.available_shifts),
            max_hours=emp.max_hours,
        )
        session.add(obj)
    await session.commit()
    return EmployeeResponse(
        id=obj.id,
        name=obj.name,
        skills=json.loads(obj.skills_json),
        available_shifts=json.loads(obj.available_shifts_json),
        max_hours=obj.max_hours,
    )


async def list_employees(session: AsyncSession) -> list[EmployeeResponse]:
    employees_by_id: dict[str, EmployeeResponse] = {}

    # 1. Standalone employees
    res = await session.execute(select(EmployeeORM))
    for obj in res.scalars().all():
        employees_by_id[obj.id] = EmployeeResponse(
            id=obj.id,
            name=obj.name,
            skills=json.loads(obj.skills_json),
            available_shifts=json.loads(obj.available_shifts_json),
            max_hours=obj.max_hours,
        )

    # 2. Employees from saved scenarios
    res_scenarios = await session.execute(select(ScenarioORM))
    for scn in res_scenarios.scalars().all():
        try:
            d = json.loads(scn.input_json)
            for e in d.get("employees", []):
                if e["id"] not in employees_by_id:
                    employees_by_id[e["id"]] = EmployeeResponse(
                        id=e["id"],
                        name=e["name"],
                        skills=e.get("skills", []),
                        available_shifts=e.get("available_shifts", []),
                        max_hours=float(e["max_hours"]),
                    )
        except Exception:
            continue

    return list(employees_by_id.values())


async def save_unit(session: AsyncSession, unit: UnitCreate) -> UnitResponse:
    obj = await session.get(UnitORM, unit.id)
    if obj:
        obj.name = unit.name
        obj.required_skills_json = json.dumps(unit.required_skills)
    else:
        obj = UnitORM(
            id=unit.id,
            name=unit.name,
            required_skills_json=json.dumps(unit.required_skills),
        )
        session.add(obj)
    await session.commit()
    return UnitResponse(
        id=obj.id,
        name=obj.name,
        required_skills=json.loads(obj.required_skills_json),
    )


async def list_units(session: AsyncSession) -> list[UnitResponse]:
    units_by_id: dict[str, UnitResponse] = {}

    res = await session.execute(select(UnitORM))
    for obj in res.scalars().all():
        units_by_id[obj.id] = UnitResponse(
            id=obj.id,
            name=obj.name,
            required_skills=json.loads(obj.required_skills_json),
        )

    res_scenarios = await session.execute(select(ScenarioORM))
    for scn in res_scenarios.scalars().all():
        try:
            d = json.loads(scn.input_json)
            for u in d.get("units", []):
                if u["id"] not in units_by_id:
                    units_by_id[u["id"]] = UnitResponse(
                        id=u["id"],
                        name=u["name"],
                        required_skills=u.get("required_skills", []),
                    )
        except Exception:
            continue

    return list(units_by_id.values())


async def save_shift(session: AsyncSession, shift: ShiftCreate) -> ShiftResponse:
    obj = await session.get(ShiftORM, shift.id)
    if obj:
        obj.name = shift.name
        obj.start_time = shift.start_time
        obj.end_time = shift.end_time
        obj.duration_hours = shift.duration_hours
    else:
        obj = ShiftORM(
            id=shift.id,
            name=shift.name,
            start_time=shift.start_time,
            end_time=shift.end_time,
            duration_hours=shift.duration_hours,
        )
        session.add(obj)
    await session.commit()
    return ShiftResponse(
        id=obj.id,
        name=obj.name,
        start_time=obj.start_time,
        end_time=obj.end_time,
        duration_hours=obj.duration_hours,
    )


async def list_shifts(session: AsyncSession) -> list[ShiftResponse]:
    shifts_by_id: dict[str, ShiftResponse] = {}

    res = await session.execute(select(ShiftORM))
    for obj in res.scalars().all():
        shifts_by_id[obj.id] = ShiftResponse(
            id=obj.id,
            name=obj.name,
            start_time=obj.start_time,
            end_time=obj.end_time,
            duration_hours=obj.duration_hours,
        )

    res_scenarios = await session.execute(select(ScenarioORM))
    for scn in res_scenarios.scalars().all():
        try:
            d = json.loads(scn.input_json)
            for s in d.get("shifts", []):
                if s["id"] not in shifts_by_id:
                    shifts_by_id[s["id"]] = ShiftResponse(
                        id=s["id"],
                        name=s["name"],
                        start_time=s["start_time"],
                        end_time=s["end_time"],
                        duration_hours=float(s["duration_hours"]),
                    )
        except Exception:
            continue

    return list(shifts_by_id.values())
