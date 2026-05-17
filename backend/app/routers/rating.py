from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from typing import List
from app.database.db import get_db
from app.models.models import Filial, KPI, KpiFact, Rating
from app.schemas.schemas import RatingResponse

router = APIRouter(prefix="/api", tags=["rating"])

@router.get("/rating", response_model=List[RatingResponse])
async def get_rating(period: date = Query(...), db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли уже рассчитанный рейтинг в таблице ratings для этого периода
    stmt = select(Rating).where(Rating.period == period).order_by(Rating.rank)
    result = await db.execute(stmt)
    existing = result.scalars().all()
    if existing:
        # Возвращаем из истории
        response = []
        for r in existing:
            filial = await db.get(Filial, r.filial_id)
            response.append(RatingResponse(
                filial_id=r.filial_id,
                filial_name=filial.name,
                period=r.period,
                score=r.score,
                rank=r.rank
            ))
        return response
    
    # 1. Получаем все KPI с весами
    kpis_stmt = select(KPI)
    kpis_res = await db.execute(kpis_stmt)
    kpis = kpis_res.scalars().all()
    if not kpis:
        raise HTTPException(status_code=404, detail="No KPI defined")
    
    # 2. Получаем все филиалы
    filials_stmt = select(Filial)
    filials_res = await db.execute(filials_stmt)
    filials = filials_res.scalars().all()
    if not filials:
        raise HTTPException(status_code=404, detail="No filials")
    
    # 3. Получаем фактические значения для каждого филиала и каждого KPI за указанный период
    facts_stmt = select(KpiFact).where(KpiFact.period == period)
    facts_res = await db.execute(facts_stmt)
    facts = facts_res.scalars().all()
    
    # Строим словарь (filial_id, kpi_id) -> value
    fact_dict = {}
    for f in facts:
        fact_dict[(f.filial_id, f.kpi_id)] = f.value
    
    # 4. Для каждого KPI найдем максимальное и минимальное значение (для нормализации)
    #    Считаем только факты за этот период
    kpi_best = {}
    for kpi in kpis:
        values = [fact_dict[(fil.id, kpi.id)] for fil in filials if (fil.id, kpi.id) in fact_dict]
        if not values:
            # если нет данных, пропускаем этот KPI или используем 0
            best = 1
        else:
            if kpi.is_higher_better:
                best = max(values)
            else:
                best = min(values)
        kpi_best[kpi.id] = best
    
    # 5. Считаем интегральный балл для каждого филиала
    scores = {}
    for fil in filials:
        total = 0.0
        for kpi in kpis:
            key = (fil.id, kpi.id)
            val = fact_dict.get(key)
            if val is None:
                # если нет факта, считаем 0 (или можно пропустить)
                continue
            best = kpi_best[kpi.id]
            if best == 0:
                norm = 0
            else:
                if kpi.is_higher_better:
                    norm = val / best
                else:
                    # чем меньше, тем лучше: нормализуем как best/val (или 1 - (val - best)/max)
                    norm = best / val if val != 0 else 0
            total += norm * kpi.weight
        scores[fil.id] = total
    
    # 6. Сортируем по убыванию балла
    sorted_filials = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # 7. Сохраняем рейтинг в таблицу ratings
    new_ratings = []
    for rank, (fil_id, score) in enumerate(sorted_filials, start=1):
        rating = Rating(filial_id=fil_id, period=period, score=score, rank=rank)
        db.add(rating)
        new_ratings.append(rating)
    await db.commit()
    
    # 8. Возвращаем результат
    response = []
    for r in new_ratings:
        filial = await db.get(Filial, r.filial_id)
        response.append(RatingResponse(
            filial_id=r.filial_id,
            filial_name=filial.name,
            period=r.period,
            score=r.score,
            rank=r.rank
        ))
    return response