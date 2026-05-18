import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.models import Filial, KPI, KpiFact
from datetime import datetime

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/kpi-structured")
async def import_kpi_structured(
    file: UploadFile = File(...),
    filial: str = Form(...),
    category: str = Form(...),
    indicator: str = Form(...),
    period: str = Form(...),  # формат "2025-01-01"
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Требуется файл Excel")
    
    try:
        # Читаем файл
        df = pd.read_excel(file.file)
        # Ожидаем колонки: Период, Значение (или просто первая и вторая)
        if len(df.columns) < 2:
            raise HTTPException(400, "Файл должен содержать как минимум две колонки: период и значение")
        
        period_col = df.columns[0]
        value_col = df.columns[1]
        
        # Находим или создаём филиал
        result = await db.execute(select(Filial).where(Filial.name == filial))
        filial_obj = result.scalar_one_or_none()
        if not filial_obj:
            filial_obj = Filial(name=filial)
            db.add(filial_obj)
            await db.flush()
        
        # Находим KPI по category+indicator
        kpi_name = f"{category} - {indicator}"
        result = await db.execute(select(KPI).where(KPI.name == kpi_name))
        kpi = result.scalar_one_or_none()
        if not kpi:
            # Создаём KPI с weight=1 (можно будет потом настроить)
            kpi = KPI(name=kpi_name, category=category, weight=1.0, target=100, is_higher_better=1)
            db.add(kpi)
            await db.flush()
        
        target_period = datetime.strptime(period, "%Y-%m-%d").date()
        rows_imported = 0
        
        # Обрабатываем каждую строку (можно загружать несколько периодов, но обычно один)
        for _, row in df.iterrows():
            row_period = pd.to_datetime(row[period_col]).date()
            value = float(row[value_col])
            
            # Если период не совпадает с указанным в форме, можно пропустить или использовать свой
            # По умолчанию используем период из формы, но можно и из файла
            # Здесь используем период из формы для всех строк (для простоты)
            # Если хотите поддержку нескольких периодов в файле, замените target_period на row_period
            
            existing = await db.execute(
                select(KpiFact).where(
                    KpiFact.filial_id == filial_obj.id,
                    KpiFact.kpi_id == kpi.id,
                    KpiFact.period == target_period
                )
            )
            fact = existing.scalar_one_or_none()
            if fact:
                fact.value = value
            else:
                db.add(KpiFact(filial_id=filial_obj.id, kpi_id=kpi.id, period=target_period, value=value))
            rows_imported += 1
            await db.flush()
        
        await db.commit()
        return {"status": "ok", "rows_imported": rows_imported, "filial": filial, "kpi": kpi_name}
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Ошибка импорта: {str(e)}")