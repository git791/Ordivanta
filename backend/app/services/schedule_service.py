import uuid
import io
import csv
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.enums import Algorithm, SolverStatus
from app.schemas.schedule import (
    SolveRequest,
    SolveResponse,
    RunSummary,
    AssignmentResponse,
    ViolationResponse,
    MetricsResponse,
)
from app.validation.input_validator import validate_scenario
from app.validation.schedule_validator import validate_assignments
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.greedy_scheduler import GreedyScheduler
from app.optimization.alns_scheduler import ALNSScheduler
from app.metrics.schedule_metrics import compute_metrics
from app.services.scenario_service import get_scenario_domain, ValidationFailedError
from app.persistence import repository


class RunNotFoundError(Exception):
    pass


class ExportNotPermittedError(Exception):
    pass


async def solve_schedule(
    session: AsyncSession, request: SolveRequest
) -> SolveResponse:
    # 1. Load scenario
    scenario = await get_scenario_domain(session, request.scenario_id)

    # 2. Input validation
    val_result = validate_scenario(scenario)
    if not val_result.is_valid:
        raise ValidationFailedError(
            f"Scenario '{scenario.id}' failed input validation",
            errors=val_result.errors,
        )

    # 3. Choose scheduler
    if request.algorithm == Algorithm.MILP:
        scheduler = MILPScheduler()
    elif request.algorithm == Algorithm.GREEDY:
        scheduler = GreedyScheduler()
    elif request.algorithm == Algorithm.ALNS:
        scheduler = ALNSScheduler()
    else:
        raise ValueError(f"Unsupported algorithm: {request.algorithm}")

    # 4. Execute optimization
    outcome = await asyncio.to_thread(
        scheduler.solve,
        scenario,
        request.objective,
        time_limit=request.time_limit_seconds,
    )

    # 5. Independent schedule validation
    schedule_val = validate_assignments(outcome.assignments, scenario)

    # 6. Compute metrics
    metrics = compute_metrics(
        assignments=outcome.assignments,
        scenario=scenario,
        runtime_seconds=outcome.runtime_seconds,
        objective_value=outcome.objective_value,
        violation_count=len(schedule_val.errors),
    )

    # 7. Build violations list
    violations: list[ViolationResponse] = []
    for issue in schedule_val.errors + schedule_val.warnings:
        violations.append(
            ViolationResponse(
                code=issue.code,
                message=issue.message,
                severity=issue.severity,
                employee_id=issue.employee_id,
                unit_id=issue.unit_id,
                shift_id=issue.shift_id,
            )
        )

    # Collect warnings
    warnings: list[str] = [w.message for w in val_result.warnings]
    warnings.extend([w.message for w in schedule_val.warnings])
    if outcome.message:
        warnings.append(outcome.message)

    # 8. Build SolveResponse DTO
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    assignment_responses = [
        AssignmentResponse(
            employee_id=a.employee_id,
            unit_id=a.unit_id,
            shift_id=a.shift_id,
            hours=a.hours,
        )
        for a in outcome.assignments
    ]

    response = SolveResponse(
        run_id=run_id,
        scenario_id=scenario.id,
        algorithm=request.algorithm,
        status=outcome.status,
        runtime_seconds=round(outcome.runtime_seconds, 4),
        objective_value=outcome.objective_value,
        assignments=assignment_responses,
        metrics=metrics,
        violations=violations,
        warnings=warnings,
        created_at=datetime.utcnow(),
    )

    # 9. Persist run
    await repository.save_run(session, response)
    return response


async def get_run(session: AsyncSession, run_id: str) -> SolveResponse:
    run = await repository.get_run(session, run_id)
    if not run:
        raise RunNotFoundError(f"Schedule run '{run_id}' not found")
    return run


async def list_runs(
    session: AsyncSession, scenario_id: str | None = None
) -> list[RunSummary]:
    return await repository.list_runs(session, scenario_id)


async def get_run_metrics(session: AsyncSession, run_id: str) -> MetricsResponse:
    run = await get_run(session, run_id)
    return run.metrics


async def export_schedule_csv(session: AsyncSession, run_id: str) -> str:
    run = await get_run(session, run_id)
    if run.status in (SolverStatus.INFEASIBLE, SolverStatus.ERROR):
        raise ExportNotPermittedError(
            f"Cannot export schedule with status {run.status.value}"
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "run_id",
        "scenario_id",
        "algorithm",
        "status",
        "employee_id",
        "unit_id",
        "shift_id",
        "hours",
    ])

    for a in run.assignments:
        writer.writerow([
            run.run_id,
            run.scenario_id,
            run.algorithm.value,
            run.status.value,
            a.employee_id,
            a.unit_id,
            a.shift_id,
            a.hours,
        ])

    return output.getvalue()
