from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import PrimaryData, Filial, Rating
from datetime import date, timedelta
from collections import defaultdict

# Максимальные баллы по показателям и категориям (из Excel)
MAX_SCORES = {
    "ЮЛ": {"p1": 45, "p2": 35, "p3": 20},
    "ФЛ": {"p1": 10, "p2": 35, "p3": 5},
    "ИКУ": {"p1": 10, "p2": 35, "p3": 5},
}

# Плановые значения реализации (норматив) – временно, пока нет таблицы
# В реальности нужно брать из БД или настроек
TARGET_REALIZATION = {
    "ЮЛ": 1_000_000,   # план для ЮЛ в месяц
    "ФЛ": 500_000,
    "ИКУ": 300_000,
}

def calculate_p1(realization, category):
    """НУР – процент выполнения плана, умноженный на max_балл (не более max)."""
    target = TARGET_REALIZATION.get(category, 1)
    if target <= 0:
        return 0
    percent = min(realization / target, 2.0)  # ограничим 200% (можно и 100%)
    max_score = MAX_SCORES[category]["p1"]
    return round(percent * max_score, 2)

def calculate_p2(realization, overdue_debt, old_overdue_debt, old_realization, category):
    """
    Оценка доли ПЗ и снижение ПЗ.
    Упрощённо: чем меньше доля ПЗ, тем лучше; плюс бонус за снижение.
    Максимум = max_score.
    """
    max_score = MAX_SCORES[category]["p2"]
    if realization <= 0:
        return 0
    # Доля ПЗ в текущем месяце
    current_ratio = overdue_debt / realization
    # Доля ПЗ в прошлом году (если данные есть)
    if old_realization and old_realization > 0:
        old_ratio = old_overdue_debt / old_realization
        reduction = max(0, old_ratio - current_ratio)  # снижение доли
    else:
        reduction = 0
    # Формула: базовые баллы за низкую долю + бонус за снижение
    # За долю 0% – 70% от max, за долю 10% – 0%. Простая линейная.
    base_score = max_score * 0.7 * (1 - min(current_ratio / 0.10, 1.0))
    bonus = max_score * 0.3 * min(reduction / 0.05, 1.0)  # если снизили на 5% – полный бонус
    return round(min(base_score + bonus, max_score), 2)

def calculate_p3(realization, debt_receivable, category):
    """Доля задолженности в объёме продаж. Чем ниже долг, тем выше балл."""
    max_score = MAX_SCORES[category]["p3"]
    if realization <= 0:
        return 0
    ratio = debt_receivable / realization
    # Линейно: при доле 0% – max баллов, при доле 30% – 0 баллов
    score = max_score * (1 - min(ratio / 0.3, 1.0))
    return round(score, 2)

async def calculate_rating_by_primary(period: date, db: AsyncSession):
    # Данные за текущий месяц
    stmt = select(PrimaryData).where(PrimaryData.period == period)
    result = await db.execute(stmt)
    records = result.scalars().all()
    if not records:
        return {"error": f"Нет первичных данных за период {period}"}

    # Данные за тот же месяц прошлого года
    last_year_period = period.replace(year=period.year - 1)
    stmt_old = select(PrimaryData).where(PrimaryData.period == last_year_period)
    result_old = await db.execute(stmt_old)
    old_records = result_old.scalars().all()
    old_data = {(r.filial_id, r.category): r for r in old_records}

    # Группируем текущие записи по филиалу и категории
    filial_cat_data = defaultdict(lambda: {})
    for rec in records:
        filial_cat_data[rec.filial_id][rec.category] = rec

    ratings_to_save = []
    for filial_id, cats in filial_cat_data.items():
        filial = await db.get(Filial, filial_id)
        if not filial:
            continue

        total_score = 0.0
        kpi_scores = {"ЮЛ": 0.0, "ФЛ": 0.0, "ИКУ": 0.0}

        for category, data in cats.items():
            # Показатель 1: НУР
            p1 = calculate_p1(data.realization, category)
            # Показатель 2: ПЗ (нужны данные за прошлый год)
            old = old_data.get((filial_id, category))
            old_overdue = old.overdue_debt if old else 0
            old_realization = old.realization if old else 0
            p2 = calculate_p2(data.realization, data.overdue_debt, old_overdue, old_realization, category)
            # Показатель 3: Доля долга
            p3 = calculate_p3(data.realization, data.debt_receivable, category)

            cat_total = p1 + p2 + p3
            kpi_scores[category] = cat_total
            total_score += cat_total

        # Сохраняем
        ratings_to_save.append({
            "filial_id": filial_id,
            "period": period,
            "score": total_score,
            "kpi1": kpi_scores["ЮЛ"],
            "kpi2": kpi_scores["ФЛ"],
            "kpi3": kpi_scores["ИКУ"],
        })

    # Удаляем старые рейтинги и вставляем новые
    from sqlalchemy import delete
    await db.execute(delete(Rating).where(Rating.period == period))
    for r in ratings_to_save:
        rating = Rating(
            filial_id=r["filial_id"],
            period=r["period"],
            score=r["score"],
            rank=0,
            kpi1=r["kpi1"],
            kpi2=r["kpi2"],
            kpi3=r["kpi3"],
        )
        db.add(rating)
    await db.commit()

    # Пересчёт рангов
    all_ratings = (await db.execute(select(Rating).where(Rating.period == period).order_by(Rating.score.desc()))).scalars().all()
    for idx, rt in enumerate(all_ratings, start=1):
        rt.rank = idx
    await db.commit()

    return [
        {"filial_id": r.filial_id, "score": r.score, "kpi1": r.kpi1, "kpi2": r.kpi2, "kpi3": r.kpi3, "rank": r.rank}
        for r in all_ratings
    ]