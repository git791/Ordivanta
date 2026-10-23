from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.database import get_session
from app.schemas.schedule import (
    SolveRequest,
    SolveResponse,
    RunSummary,
    MetricsResponse,
)
from app.services import schedule_service

router = APIRouter()


@router.post(
    "/schedules/solve",
    response_model=SolveResponse,
    status_code=status.HTTP_200_OK,
)
async def solve_schedule_endpoint(
    request: SolveRequest, session: AsyncSession = Depends(get_session)
):
    return await schedule_service.solve_schedule(session, request)


@router.get("/schedules", response_model=list[RunSummary])
async def list_runs(
    scenario_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    return await schedule_service.list_runs(session, scenario_id=scenario_id)


@router.get("/schedules/{run_id}", response_model=SolveResponse)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    return await schedule_service.get_run(session, run_id)


@router.get("/schedules/{run_id}/metrics", response_model=MetricsResponse)
async def get_run_metrics(
    run_id: str, session: AsyncSession = Depends(get_session)
):
    return await schedule_service.get_run_metrics(session, run_id)


@router.get("/schedules/{run_id}/export")
async def export_schedule_csv(
    run_id: str, session: AsyncSession = Depends(get_session)
):
    csv_data = await schedule_service.export_schedule_csv(session, run_id)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=schedule_{run_id}.csv"
        },
    )
