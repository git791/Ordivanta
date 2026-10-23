import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.persistence.database import Base, get_session
from app.main import app


@pytest.fixture
def minimal_valid_scenario() -> Scenario:
    """Fixture for a minimal valid scenario: 3 employees, 1 unit, 1 shift, demand=2."""
    return Scenario(
        id="scenario_minimal",
        name="Minimal Valid Scenario",
        employees=[
            Employee(
                id="E1",
                name="Alice",
                skills=["assembly"],
                available_shifts=["S1"],
                max_hours=8.0,
            ),
            Employee(
                id="E2",
                name="Bob",
                skills=["assembly"],
                available_shifts=["S1"],
                max_hours=8.0,
            ),
            Employee(
                id="E3",
                name="Charlie",
                skills=["assembly"],
                available_shifts=["S1"],
                max_hours=8.0,
            ),
        ],
        units=[
            ProductionUnit(
                id="U1",
                name="Assembly Unit",
                required_skills=["assembly"],
            )
        ],
        shifts=[
            Shift(
                id="S1",
                name="Morning Shift",
                start_time="08:00",
                end_time="16:00",
                duration_hours=8.0,
            )
        ],
        demands=[
            Demand(
                unit_id="U1",
                shift_id="S1",
                required_headcount=2,
            )
        ],
    )


@pytest.fixture
def infeasible_scenario() -> Scenario:
    """Fixture for an infeasible scenario: demand=5, only 2 qualified employees."""
    return Scenario(
        id="scenario_infeasible_fixture",
        name="Infeasible Scenario Fixture",
        employees=[
            Employee(
                id="E1",
                name="Alice",
                skills=["welding"],
                available_shifts=["S1"],
                max_hours=8.0,
            ),
            Employee(
                id="E2",
                name="Bob",
                skills=["welding"],
                available_shifts=["S1"],
                max_hours=8.0,
            ),
        ],
        units=[
            ProductionUnit(
                id="U1",
                name="Welding Unit",
                required_skills=["welding"],
            )
        ],
        shifts=[
            Shift(
                id="S1",
                name="Day Shift",
                start_time="08:00",
                end_time="16:00",
                duration_hours=8.0,
            )
        ],
        demands=[
            Demand(
                unit_id="U1",
                shift_id="S1",
                required_headcount=5,
            )
        ],
    )


@pytest_asyncio.fixture
async def test_session():
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()
