from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.models import Filial as FilialModel
from app.schemas.schemas import FilialCreate, Filial

router = APIRouter(prefix="/api/filials", tags=["filials"])

@router.post("/", response_model=Filial)
async def create_filial(filial: FilialCreate, db: AsyncSession = Depends(get_db)):
    db_filial = FilialModel(name=filial.name, region=filial.region)
    db.add(db_filial)
    await db.commit()
    await db.refresh(db_filial)
    return db_filial

@router.get("/", response_model=list[Filial])
async def get_filials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FilialModel))
    return result.scalars().all()