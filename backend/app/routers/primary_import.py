import pandas as pd
import xml.etree.ElementTree as ET
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.models import Filial, PrimaryData
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/primary", tags=["primary"])

@router.post("/import")
async def import_primary_data(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['xlsx', 'xls', 'csv', 'xml']:
        raise HTTPException(400, "Поддерживаются форматы .xlsx, .xls, .csv, .xml")

    content = await file.read()
    logger.info(f"Файл {file.filename} прочитан, размер {len(content)} байт")
    
    # Чтение в зависимости от расширения
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(pd.io.BytesIO(content))
            logger.info(f"Excel прочитан, строк: {len(df)}")
        elif ext == 'csv':
            df = pd.read_csv(pd.io.StringIO(content.decode('utf-8-sig')))
            logger.info(f"CSV прочитан, строк: {len(df)}")
        else:  # xml
            root = ET.fromstring(content)
            data = []
            for elem in root.findall('.//record'):
                attrs = elem.attrib
                required_attrs = ['филиал', 'период', 'категория', 'accrued', 'advances', 
                                  'realization', 'debt_receivable', 'overdue_debt']
                if not all(attr in attrs for attr in required_attrs):
                    logger.warning(f"Пропущен элемент {attrs} – не хватает атрибутов")
                    continue
                data.append({col: attrs[col] for col in required_attrs})
            if not data:
                raise HTTPException(400, "XML не содержит корректных записей с нужными атрибутами")
            df = pd.DataFrame(data)
            logger.info(f"XML прочитан, строк: {len(df)}")
    except Exception as e:
        logger.error(f"Ошибка чтения файла: {e}")
        raise HTTPException(400, f"Ошибка чтения файла: {e}")

    # Проверка наличия нужных колонок
    required_columns = {"филиал", "период", "категория", "accrued", "advances", 
                        "realization", "debt_receivable", "overdue_debt"}
    missing = required_columns - set(df.columns)
    if missing:
        logger.error(f"Отсутствуют колонки: {missing}")
        raise HTTPException(400, f"Не хватает колонок: {missing}. В файле есть: {list(df.columns)}")

    stats = {"added": 0, "updated": 0, "errors": []}

    for idx, row in df.iterrows():
        try:
            filial_name = str(row["филиал"]).strip()
            period = pd.to_datetime(row["период"]).date()
            category = str(row["категория"]).strip()
            accrued = float(row["accrued"])
            advances = float(row["advances"])
            realization = float(row["realization"])
            debt_receivable = float(row["debt_receivable"])
            overdue_debt = float(row["overdue_debt"])

            # Находим или создаём филиал
            result = await db.execute(select(Filial).where(Filial.name == filial_name))
            filial = result.scalar_one_or_none()
            if not filial:
                filial = Filial(name=filial_name)
                db.add(filial)
                await db.flush()
                logger.info(f"Создан новый филиал: {filial_name} (id={filial.id})")
            else:
                logger.debug(f"Филиал найден: {filial_name} (id={filial.id})")

            # Проверяем существование записи
            stmt = select(PrimaryData).where(
                PrimaryData.filial_id == filial.id,
                PrimaryData.period == period,
                PrimaryData.category == category
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if existing:
                existing.accrued = accrued
                existing.advances = advances
                existing.realization = realization
                existing.debt_receivable = debt_receivable
                existing.overdue_debt = overdue_debt
                stats["updated"] += 1
                logger.debug(f"Обновлена запись для {filial_name}, {period}, {category}")
            else:
                new_data = PrimaryData(
                    filial_id=filial.id,
                    period=period,
                    category=category,
                    accrued=accrued,
                    advances=advances,
                    realization=realization,
                    debt_receivable=debt_receivable,
                    overdue_debt=overdue_debt
                )
                db.add(new_data)
                stats["added"] += 1
                logger.debug(f"Добавлена новая запись для {filial_name}, {period}, {category}")

        except Exception as e:
            error_msg = f"Строка {idx+2}: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

    await db.commit()
    logger.info(f"Импорт завершён: добавлено {stats['added']}, обновлено {stats['updated']}, ошибок {len(stats['errors'])}")
    return {"status": "ok", "stats": stats}