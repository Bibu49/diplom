from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import List

from app.database.db import get_db
from app.models.models import Filial, KPI, KpiFact, Rating
from app.schemas.schemas import RatingResponse

router = APIRouter(prefix="/api", tags=["rating"])


class FormulaEngine:

    @staticmethod
    def performance(accrued: float, paid: float):
        if accrued == 0:
            return 0

        return paid / accrued

    @staticmethod
    def delta(fact: float, norm: float):
        return fact - norm

    @staticmethod
    def score(delta_percent: float, max_score: float = 30):
        """
        Excel:
        =(1+0.3*B4/1%)*30
        """

        score = (
            1 + 0.3 * (delta_percent / 0.01)
        ) * max_score

        return max(score, 0)

    @staticmethod
    def lower_better_score(value, best, weight):
        """
        Для KPI где меньше = лучше
        """

        if value == 0:
            return 0

        ratio = best / value

        return ratio * weight

    @staticmethod
    def higher_better_score(value, best, weight):
        """
        Для KPI где больше = лучше
        """

        if best == 0:
            return 0

        ratio = value / best

        return ratio * weight


# =====================================================
# MAIN RATING ENDPOINT
# =====================================================

@router.get("/rating", response_model=List[RatingResponse])
async def get_rating(
    period: date = Query(...),
    db: AsyncSession = Depends(get_db)
):

    # =====================================================
    # 1. Проверка существующего рейтинга
    # =====================================================

    stmt = (
        select(Rating)
        .where(Rating.period == period)
        .order_by(Rating.rank)
    )

    result = await db.execute(stmt)

    existing = result.scalars().all()

    if existing:

        response = []

        for r in existing:

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

    # =====================================================
    # 2. Загружаем KPI
    # =====================================================

    kpis_stmt = select(KPI)

    kpis_res = await db.execute(kpis_stmt)

    kpis = kpis_res.scalars().all()

    if not kpis:
        raise HTTPException(
            status_code=404,
            detail="No KPI defined"
        )

    # =====================================================
    # 3. Загружаем филиалы
    # =====================================================

    filials_stmt = select(Filial)

    filials_res = await db.execute(filials_stmt)

    filials = filials_res.scalars().all()

    if not filials:
        raise HTTPException(
            status_code=404,
            detail="No filials"
        )

    # =====================================================
    # 4. Загружаем KPI факты
    # =====================================================

    facts_stmt = (
        select(KpiFact)
        .where(KpiFact.period == period)
    )

    facts_res = await db.execute(facts_stmt)

    facts = facts_res.scalars().all()

    if not facts:
        raise HTTPException(
            status_code=404,
            detail="No KPI facts for selected period"
        )

    # =====================================================
    # 5. Строим словарь фактов
    # =====================================================

    fact_dict = {}

    for f in facts:
        fact_dict[(f.filial_id, f.kpi_id)] = f.value

    # =====================================================
    # 6. Лучшие значения KPI
    # =====================================================

    kpi_best = {}

    for kpi in kpis:

        values = [
            fact_dict[(fil.id, kpi.id)]
            for fil in filials
            if (fil.id, kpi.id) in fact_dict
        ]

        if not values:
            kpi_best[kpi.id] = 1
            continue

        if kpi.is_higher_better:
            kpi_best[kpi.id] = max(values)
        else:
            kpi_best[kpi.id] = min(values)

    # =====================================================
    # 7. РАСЧЕТ EXCEL KPI SCORE
    # =====================================================

    scores = {}

    for fil in filials:

        total_score = 0.0

        for kpi in kpis:

            key = (fil.id, kpi.id)

            value = fact_dict.get(key)

            if value is None:
                continue

            best = kpi_best[kpi.id]

            # =============================================
            # HIGHER BETTER
            # =============================================

            if kpi.is_higher_better:

                base_score = FormulaEngine.higher_better_score(
                    value=value,
                    best=best,
                    weight=kpi.weight
                )

            # =============================================
            # LOWER BETTER
            # =============================================

            else:

                base_score = FormulaEngine.lower_better_score(
                    value=value,
                    best=best,
                    weight=kpi.weight
                )

            # =============================================
            # EXCEL DELTA CALCULATION
            # =============================================

            # Норматив 95%
            # Можно хранить в БД позже

            norm = 0.95

            delta = FormulaEngine.delta(
                base_score,
                norm
            )

            # =============================================
            # EXCEL SCORE FORMULA
            # =============================================

            final_score = FormulaEngine.score(
                delta_percent=delta,
                max_score=kpi.weight
            )

            total_score += final_score

        scores[fil.id] = round(total_score, 2)

    # =====================================================
    # 8. СОРТИРОВКА РЕЙТИНГА
    # =====================================================

    sorted_filials = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # =====================================================
    # 9. СОХРАНЕНИЕ В БД
    # =====================================================

    new_ratings = []

    for rank, (fil_id, score) in enumerate(
        sorted_filials,
        start=1
    ):

        rating = Rating(
            filial_id=fil_id,
            period=period,
            score=score,
            rank=rank
        )

        db.add(rating)

        new_ratings.append(rating)

    await db.commit()

    # =====================================================
    # 10. RESPONSE
    # =====================================================

    response = []

    for r in new_ratings:

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
