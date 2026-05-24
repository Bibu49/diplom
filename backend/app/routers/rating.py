from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from typing import List

from app.database.db import get_db
from app.models.models import Filial, Rating, PrimaryData
from app.schemas.schemas import RatingResponse
from app.services.rating_calculator import calculate_rating_by_primary

router = APIRouter(prefix="/api", tags=["rating"])


@router.get("/rating", response_model=List[RatingResponse])
async def get_rating(
    period: date = Query(...),
    db: AsyncSession = Depends(get_db)
):

    stmt = (
        select(Rating)
        .where(Rating.period == period)
        .order_by(Rating.rank)
    )

    result = await db.execute(stmt)

    ratings = result.scalars().all()

    if not ratings:
        return []

    primary_stmt = (
        select(
            PrimaryData.filial_id,
            func.sum(PrimaryData.realization).label('kpi1'),
            func.sum(PrimaryData.debt_receivable).label('kpi2'),
            func.sum(PrimaryData.overdue_debt).label('kpi3')
        )
        .where(PrimaryData.period == period)
        .group_by(PrimaryData.filial_id)
    )
    primary_result = await db.execute(primary_stmt)
    kpi_map = {
        row.filial_id: (row.kpi1 or 0.0, row.kpi2 or 0.0, row.kpi3 or 0.0)
        for row in primary_result
    }

    response = []

    for r in ratings:

        filial = await db.get(Filial, r.filial_id)

        response.append(
            RatingResponse(
                filial_id=r.filial_id,
                filial_name=filial.name,
                period=r.period,
                score=r.score,
                rank=r.rank,
                kpi1=r.kpi1,
                kpi2=r.kpi2,
                kpi3=r.kpi3
            )
        )
    return response


@router.post("/calculate-from-primary")
async def calculate_rating_from_primary(
    period: date,
    db: AsyncSession = Depends(get_db)
):
    result = await calculate_rating_by_primary(period, db)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "ok", "period": period.isoformat(), "ratings": result}

@router.get("/rating/year")
async def get_yearly_rating(
    year: int = Query(..., description="Год, например 2025"),
    db: AsyncSession = Depends(get_db)
):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Выбираем все записи рейтингов за год
    stmt = select(Rating).where(
        Rating.period >= start_date,
        Rating.period <= end_date
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    if not ratings:
        return []


    from collections import defaultdict
    filial_data = defaultdict(lambda: {
        'scores': [],
        'kpi1_list': [],
        'kpi2_list': [],
        'kpi3_list': []
    })

    for r in ratings:
        filial_data[r.filial_id]['scores'].append(r.score)
        if r.kpi1 is not None:
            filial_data[r.filial_id]['kpi1_list'].append(r.kpi1)
        if r.kpi2 is not None:
            filial_data[r.filial_id]['kpi2_list'].append(r.kpi2)
        if r.kpi3 is not None:
            filial_data[r.filial_id]['kpi3_list'].append(r.kpi3)

    # Формируем ответ
    response = []
    for filial_id, data in filial_data.items():
        # Получаем название филиала
        filial = await db.get(Filial, filial_id)
        filial_name = filial.name if filial else "Неизвестно"

        # Средний интегральный балл
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0.0

        # Средние по трём показателям
        avg_kpi1 = sum(data['kpi1_list']) / len(data['kpi1_list']) if data['kpi1_list'] else 0.0
        avg_kpi2 = sum(data['kpi2_list']) / len(data['kpi2_list']) if data['kpi2_list'] else 0.0
        avg_kpi3 = sum(data['kpi3_list']) / len(data['kpi3_list']) if data['kpi3_list'] else 0.0

        response.append({
            "filial_id": filial_id,
            "filial_name": filial_name,
            "score": round(avg_score, 2),
            "kpi1": round(avg_kpi1, 2),
            "kpi2": round(avg_kpi2, 2),
            "kpi3": round(avg_kpi3, 2),
            "rank": 0,  # временно, позже пересчитаем
            "months_count": len(data['scores'])
        })

    # Сортируем по убыванию среднего балла
    response.sort(key=lambda x: x["score"], reverse=True)

    # Присваиваем ранги
    for idx, item in enumerate(response, start=1):
        item["rank"] = idx

    return response