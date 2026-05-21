from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import PrimaryData, Filial, Rating
from datetime import date, timedelta
import math

async def calculate_rating_by_primary(period: date, db: AsyncSession):
    """
    period: дата отчётного месяца (например, 2025-01-01)
    """
    # Получаем все первичные данные за указанный период
    stmt = select(PrimaryData).where(PrimaryData.period == period)
    rows = await db.execute(stmt)
    rows = rows.scalars().all()
    if not rows:
        return {"error": "Нет первичных данных за указанный период"}

    # Группируем по филиалам и категориям (в каждой категории свои баллы, но в итоговый рейтинг суммируем баллы по всем категориям для филиала)
    # Для простоты будем считать, что каждый филиал имеет данные по трём категориям (ЮЛ, ФЛ, ИКУ). Если каких-то нет, пропускаем.
    filial_scores = {}  # {filial_id: total_score}

    # Для каждой записи (филиал, категория, период) рассчитываем баллы по трём показателям
    for rec in rows:
        filial_id = rec.filial_id
        category = rec.category
        accrued = rec.accrued
        advances = rec.advances
        realization = rec.realization
        debt_receivable = rec.debt_receivable
        overdue_debt = rec.overdue_debt

        # --- 1. Расчёт НУР, ФУР, отклонения и баллов ---
        # НУР = (авансы + дебиторка) / начислено
        if accrued == 0:
            nur = 0
        else:
            nur = (advances + debt_receivable) / accrued
        # ФУР = реализация / начислено
        fur = realization / accrued if accrued != 0 else 0
        delta = fur - nur   # отклонение (может быть отрицательным)

        # Баллы за НУР (по аналогии с Excel, но упрощённо)
        # За основу берём максимальный балл для данной категории (из файлов: ЮЛ – 30, ФЛ – 5, ИКУ – 5)
        if category == 'ЮЛ':
            max_score_nur = 30
            max_bonus_nur = 15
            coeff = 0.3
        else:  # ФЛ или ИКУ
            max_score_nur = 5
            max_bonus_nur = 5
            coeff = 0.2

        if delta > 0:
            score_nur = max_score_nur
            bonus_nur = max_bonus_nur
        else:
            raw_score = (1 + coeff * (delta / 0.01)) * max_score_nur
            score_nur = max(0.0, raw_score)
            raw_bonus = (1 + 0.1 * (delta / 0.01)) * max_bonus_nur - max_bonus_nur
            bonus_nur = max(0.0, raw_bonus)
            if bonus_nur > max_bonus_nur:
                bonus_nur = max_bonus_nur

        # --- 2. Доля задолженности в объёме продаж (ДЗ) ---
        if realization == 0:
            debt_share = 0
        else:
            debt_share = debt_receivable / realization   # доля ДЗ

        # Целевое значение (норматив) зависит от категории: для ЮЛ – 0.3 (30%), для ФЛ и ИКУ – тоже 0.3 (можно уточнить)
        target_debt_share = 0.3
        max_score_debt = 15 if category == 'ЮЛ' else 5   # из Excel: ЮЛ – 15, ФЛ/ИКУ – 5
        if debt_share <= target_debt_share:
            score_debt = max_score_debt
        else:
            # Штраф: чем выше доля, тем меньше баллов
            score_debt = max(0, max_score_debt * (1 - (debt_share - target_debt_share) / target_debt_share))

        # --- 3. Доля просроченной задолженности (ПЗ) и её снижение ---
        if realization == 0:
            overdue_share = 0
        else:
            overdue_share = overdue_debt / realization

        # Норматив ПЗ: для ЮЛ – 0.015, для ФЛ – 0.08, для ИКУ – 0.02
        if category == 'ЮЛ':
            target_overdue_share = 0.015
            max_score_overdue = 20
            max_bonus_overdue = 15
        elif category == 'ФЛ':
            target_overdue_share = 0.08
            max_score_overdue = 20
            max_bonus_overdue = 15
        else:  # ИКУ
            target_overdue_share = 0.02
            max_score_overdue = 20
            max_bonus_overdue = 15

        # Балл за долю ПЗ
        if overdue_share < target_overdue_share:
            score_overdue = max_score_overdue
        elif overdue_share > target_overdue_share:
            score_overdue = target_overdue_share / overdue_share * max_score_overdue
        else:
            score_overdue = max_score_overdue

        # Снижение ПЗ: требуется значение за прошлый год
        prev_period = period.replace(year=period.year - 1)
        prev_stmt = select(PrimaryData).where(
            PrimaryData.filial_id == filial_id,
            PrimaryData.category == category,
            PrimaryData.period == prev_period
        )
        prev_rec = (await db.execute(prev_stmt)).scalar_one_or_none()
        if prev_rec and prev_rec.realization != 0:
            prev_overdue_share = prev_rec.overdue_debt / prev_rec.realization
            if prev_overdue_share > 0:
                improvement = max(0, (prev_overdue_share - overdue_share) / prev_overdue_share)
            else:
                improvement = 1 if overdue_share == 0 else 0
        else:
            improvement = 0

        # Бонус за снижение
        bonus_overdue = max_bonus_overdue * min(improvement, 1.0)

        # --- Итоговый балл для данной категории филиала (сумма трёх показателей, бонусы не входят в рейтинг, но можно добавить) ---
        category_score = score_nur + score_debt + score_overdue   # бонусы не включаем, как в Excel (они отдельно)

        # Суммируем по филиалу (складываем баллы по категориям)
        if filial_id not in filial_scores:
            filial_scores[filial_id] = 0
        filial_scores[filial_id] += category_score

    if not filial_scores:
        return {"error": "Не удалось рассчитать баллы ни для одного филиала"}

    # Сортируем филиалы по сумме баллов (убывание)
    sorted_filials = sorted(filial_scores.items(), key=lambda x: x[1], reverse=True)

    # Сохраняем рейтинг в таблицу Rating
    await db.execute(Rating.__table__.delete().where(Rating.period == period))
    for rank, (filial_id, total_score) in enumerate(sorted_filials, start=1):
        rating = Rating(
            filial_id=filial_id,
            period=period,
            score=total_score,
            rank=rank
        )
        db.add(rating)
    await db.commit()

    # Возвращаем результат
    result = []
    for filial_id, score in sorted_filials:
        filial = await db.get(Filial, filial_id)
        result.append({
            "filial_id": filial_id,
            "filial_name": filial.name if filial else "Неизвестно",
            "score": score,
            "rank": result[-1]["rank"] + 1 if result else 1  # корректно проставить rank
        })
    # Пересчитаем rank по порядку
    for i, item in enumerate(result, 1):
        item["rank"] = i
    return result