from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import List

from app.database.db import get_db
from app.models.models import Filial, Rating
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

    response = []

    for r in ratings:

        filial = await db.get(Filial, r.filial_id)

        response.append(
            RatingResponse(
                filial_id=r.filial_id,
                filial_name=filial.name,
                period=r.period,
                score=r.score,
                rank=r.rank
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
    """
    Возвращает средний рейтинг (score) для каждого филиала за все месяцы указанного года.
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Выбираем все рейтинги за год
    stmt = select(Rating).where(
        Rating.period >= start_date,
        Rating.period <= end_date
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    if not ratings:
        return []

    # Группируем по филиалу и вычисляем средний score
    from collections import defaultdict
    filial_scores = defaultdict(list)
    filial_names = {}

    for r in ratings:
        filial_scores[r.filial_id].append(r.score)
        if r.filial_id not in filial_names:
            filial = await db.get(Filial, r.filial_id)
            if filial:
                filial_names[r.filial_id] = filial.name
            else:
                filial_names[r.filial_id] = "Неизвестно"

    response = []
    for filial_id, scores in filial_scores.items():
        avg_score = sum(scores) / len(scores)
        response.append({
            "filial_id": filial_id,
            "filial_name": filial_names.get(filial_id, "Неизвестно"),
            "score": round(avg_score, 2),
            "rank" : 0,
            "months_count": len(scores)
        })

    # Сортируем по убыванию среднего балла
    response.sort(key=lambda x: x["score"], reverse=True)

    # Присваиваем места (ранги)
    for idx, item in enumerate(response, start=1):
        item["rank"] = idx

    return response
