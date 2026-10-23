from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.database import get_session
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioSummary,
    ValidationResponse,
)
from app.services import scenario_service

router = APIRouter()


@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(session: AsyncSession = Depends(get_session)):
    return await scenario_service.list_scenarios(session)


@router.post(
    "/scenarios",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    data: ScenarioCreate, session: AsyncSession = Depends(get_session)
):
    return await scenario_service.create_scenario(session, data)


@router.post("/scenarios/sample", response_model=ScenarioResponse)
async def load_sample(session: AsyncSession = Depends(get_session)):
    return await scenario_service.load_sample_scenario(session)


@router.get("/scenarios/{id}", response_model=ScenarioResponse)
async def get_scenario(id: str, session: AsyncSession = Depends(get_session)):
    return await scenario_service.get_scenario(session, id)


@router.post("/scenarios/{id}/validate", response_model=ValidationResponse)
async def validate_scenario(
    id: str, session: AsyncSession = Depends(get_session)
):
    return await scenario_service.validate_scenario_by_id(session, id)


@router.delete("/scenarios/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(id: str, session: AsyncSession = Depends(get_session)):
    await scenario_service.delete_scenario(session, id)
    return None
