from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.models import KpiFact as FactModel
from app.schemas.schemas import KpiFactCreate

router = APIRouter(prefix="/api/facts", tags=["facts"])

@router.post("/")
async def create_fact(fact: KpiFactCreate, db: AsyncSession = Depends(get_db)):
    db_fact = FactModel(
        filial_id=fact.filial_id,
        kpi_id=fact.kpi_id,
        period=fact.period,
        value=fact.value
    )
    db.add(db_fact)
    await db.commit()
    await db.refresh(db_fact)
    return {"message": "Fact created", "id": db_fact.id}