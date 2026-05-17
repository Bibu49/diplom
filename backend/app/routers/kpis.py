from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.models import KPI as KPIModel
from app.schemas.schemas import KPICreate, KPI

router = APIRouter(prefix="/api/kpis", tags=["kpis"])

@router.post("/", response_model=KPI)
async def create_kpi(kpi: KPICreate, db: AsyncSession = Depends(get_db)):
    db_kpi = KPIModel(**kpi.dict())
    db.add(db_kpi)
    await db.commit()
    await db.refresh(db_kpi)
    return db_kpi

@router.get("/", response_model=list[KPI])
async def get_kpis(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KPIModel))
    return result.scalars().all()