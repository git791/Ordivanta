from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Automatically seed default ground-truth manufacturing benchmark scenarios if database is empty
    from app.persistence.repository import ScenarioORM, save_scenario
    from app.datasets.registry import dataset_registry
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ScenarioORM).limit(1))
        if not result.scalar_one_or_none():
            for inst_id in [
                "mfg_standard_sample",
                "mfg_high_demand_feasible",
                "mfg_shortage_infeasible",
            ]:
                try:
                    scenario, _ = dataset_registry.load_scenario(
                        "synthetic_manufacturing", inst_id
                    )
                    await save_scenario(session, scenario)
                except Exception as e:
                    print(f"Notice: auto-seed {inst_id} skipped: {e}")


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
