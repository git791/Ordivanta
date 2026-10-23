from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.database import get_session
from app.persistence import repository
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.schemas.scenario import UnitCreate, UnitResponse, ShiftCreate, ShiftResponse

router = APIRouter()


@router.get("/employees", response_model=list[EmployeeResponse])
async def get_employees(session: AsyncSession = Depends(get_session)):
    return await repository.list_employees(session)


@router.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    data: EmployeeCreate, session: AsyncSession = Depends(get_session)
):
    return await repository.save_employee(session, data)


@router.get("/units", response_model=list[UnitResponse])
async def get_units(session: AsyncSession = Depends(get_session)):
    return await repository.list_units(session)


@router.post(
    "/units",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_unit(
    data: UnitCreate, session: AsyncSession = Depends(get_session)
):
    return await repository.save_unit(session, data)


@router.get("/shifts", response_model=list[ShiftResponse])
async def get_shifts(session: AsyncSession = Depends(get_session)):
    return await repository.list_shifts(session)


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shift(
    data: ShiftCreate, session: AsyncSession = Depends(get_session)
):
    return await repository.save_shift(session, data)
