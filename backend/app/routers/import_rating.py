import pandas as pd
import csv
import xml.etree.ElementTree as ET
import io
from io import StringIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.db import get_db
from app.models.models import Filial, Rating
from datetime import datetime

router = APIRouter(prefix="/api/import", tags=["import"])


def parse_excel(content: bytes) -> list:
    """Парсит Excel-файл (Общий рейтинг.xlsx) и возвращает список (филиал, балл)."""
    df = pd.read_excel(io.BytesIO(content), sheet_name=0, header=None)
    header_row = None
    for idx in range(min(30, len(df))):
        if str(df.iloc[idx, 2]).strip() == "Филиал":
            header_row = idx
            break
    if header_row is None:
        raise HTTPException(400, "Не найден заголовок 'Филиал'")
    data = []
    for i in range(header_row + 1, len(df)):
        filial_name = df.iloc[i, 2]
        if pd.isna(filial_name) or str(filial_name).strip() == "":
            continue
        score = df.iloc[i, 4]  # столбец E
        if pd.isna(score):
            continue
        data.append((str(filial_name).strip(), float(score)))
    return data


def parse_csv(content: bytes) -> list:
    """Парсит CSV-файл. Поддерживает разделители , ; \t, с заголовком или без."""
    data = []
    content_str = content.decode('utf-8-sig')
    for delimiter in [',', ';', '\t']:
        try:
            reader = csv.reader(StringIO(content_str), delimiter=delimiter)
            rows = list(reader)
            if not rows:
                continue
            # Определяем наличие заголовка: если первая строка не содержит число во второй колонке
            is_header = False
            if len(rows[0]) >= 2:
                try:
                    float(rows[0][1])
                except ValueError:
                    is_header = True
            start = 1 if is_header else 0
            for row in rows[start:]:
                if len(row) < 2:
                    continue
                filial = row[0].strip()
                try:
                    score = float(row[1].replace(',', '.'))
                except ValueError:
                    continue
                data.append((filial, score))
            if data:
                break  # успешно прочитали
        except Exception:
            continue
    if not data:
        raise HTTPException(400, "Не удалось разобрать CSV. Ожидается формат: филиал,балл (разделитель , ; или табуляция)")
    return data


def parse_xml(content: bytes) -> list:
    """Парсит XML-файл с элементами <rating> (атрибуты filial/score или дочерние элементы)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise HTTPException(400, "Некорректный XML")
    data = []
    for rating_elem in root.findall('.//rating'):
        # Вариант 1: атрибуты
        filial = rating_elem.get('filial')
        score_str = rating_elem.get('score')
        if filial is not None and score_str is not None:
            try:
                score = float(score_str.replace(',', '.'))
                data.append((filial.strip(), score))
                continue
            except ValueError:
                pass
        # Вариант 2: дочерние элементы
        filial_elem = rating_elem.find('filial')
        score_elem = rating_elem.find('score')
        if filial_elem is not None and score_elem is not None:
            filial = filial_elem.text
            score_str = score_elem.text
            if filial and score_str:
                try:
                    score = float(score_str.replace(',', '.'))
                    data.append((filial.strip(), score))
                except ValueError:
                    pass
    if not data:
        raise HTTPException(400, "Не найдены элементы rating с атрибутами filial/score или дочерними filial/score")
    return data


@router.post("/rating")
async def import_rating(
    file: UploadFile = File(...),
    period: str = Form(...),   # формат "2025-01-01"
    db: AsyncSession = Depends(get_db)
):
    # Проверка расширения
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['xlsx', 'xls', 'csv', 'xml']:
        raise HTTPException(400, "Поддерживаются только файлы .xlsx, .xls, .csv, .xml")

    content = await file.read()
    period_date = datetime.strptime(period, "%Y-%m-%d").date()

    try:
        if ext in ['xlsx', 'xls']:
            data = parse_excel(content)
        elif ext == 'csv':
            data = parse_csv(content)
        elif ext == 'xml':
            data = parse_xml(content)
        else:
            raise HTTPException(400, "Неподдерживаемый формат")
    except Exception as e:
        raise HTTPException(400, f"Ошибка парсинга файла: {str(e)}")

    if not data:
        raise HTTPException(400, "Не найдено данных о филиалах")

    # Сортируем по убыванию баллов
    data.sort(key=lambda x: x[1], reverse=True)

    # Удаляем старый рейтинг за период
    await db.execute(delete(Rating).where(Rating.period == period_date))

    # Сохраняем новые записи
    for rank, (filial_name, score) in enumerate(data, start=1):
        result = await db.execute(select(Filial).where(Filial.name == filial_name))
        filial = result.scalar_one_or_none()
        if not filial:
            filial = Filial(name=filial_name)
            db.add(filial)
            await db.flush()
        rating = Rating(
            filial_id=filial.id,
            period=period_date,
            score=score,
            rank=rank
        )
        db.add(rating)

    await db.commit()
    return {"status": "ok", "imported": len(data), "period": period}