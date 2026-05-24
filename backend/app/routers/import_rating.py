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
    """
    Парсит Excel-файл.
    Ожидается структура: строка с заголовком "Филиал".
    Столбцы:
        C (индекс 2) – Филиал
        D (индекс 3) – Интегральный балл
        G (индекс 6) – ЮЛ
        J (индекс 9) – ФЛ
        M (индекс 12) – ИКУ
    """
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
        # Интегральный балл
        score = df.iloc[i, 3]
        if pd.isna(score):
            continue
        # Показатели
        yul = df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else 0.0
        fl = df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else 0.0
        iku = df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else 0.0
        data.append((str(filial_name).strip(), float(score), float(yul), float(fl), float(iku)))
    return data


def parse_csv(content: bytes) -> list:
    """
    Парсит CSV-файл.
    Поддерживает разделители , ; \t.
    Если есть заголовок, ищет колонки по именам:
        'филиал', 'общий балл' (или 'score'), 'юл', 'фл', 'ику'
    Если заголовка нет – ожидает порядок: филиал, общий_балл, юл, фл, ику.
    """
    content_str = content.decode('utf-8-sig')
    for delimiter in [',', ';', '\t']:
        try:
            reader = csv.reader(StringIO(content_str), delimiter=delimiter)
            rows = list(reader)
            if not rows:
                continue

            # Пытаемся определить, есть ли заголовок
            header = None
            start_row = 0
            # Если первая строка содержит нечисловые значения в колонке баллов – считаем её заголовком
            if len(rows[0]) >= 2:
                try:
                    float(rows[0][1])
                    header = None  # нет заголовка
                except ValueError:
                    header = [col.lower().strip() for col in rows[0]]
                    start_row = 1

            # Отображение имён колонок (если есть заголовок)
            col_map = {}
            if header:
                # ожидаемые имена
                expected = {'филиал', 'общий балл', 'score', 'юл', 'фл', 'ику'}
                for idx, name in enumerate(header):
                    if name in expected:
                        col_map[name] = idx
                # Проверяем, что нашли нужные
                if 'филиал' not in col_map or ('общий балл' not in col_map and 'score' not in col_map):
                    # не удалось распознать – пробуем без заголовка
                    header = None
                    start_row = 0

            data = []
            for row in rows[start_row:]:
                if len(row) < 2:
                    continue
                if header:
                    filial = row[col_map.get('филиал', 0)].strip()
                    score = float(row[col_map.get('общий балл', col_map.get('score', 1))].replace(',', '.'))
                    yul = float(row[col_map.get('юл', 2)].replace(',', '.')) if len(row) > col_map.get('юл', 2) else 0.0
                    fl = float(row[col_map.get('фл', 3)].replace(',', '.')) if len(row) > col_map.get('фл', 3) else 0.0
                    iku = float(row[col_map.get('ику', 4)].replace(',', '.')) if len(row) > col_map.get('ику', 4) else 0.0
                else:
                    # без заголовка: позиции 0,1,2,3,4
                    filial = row[0].strip()
                    score = float(row[1].replace(',', '.'))
                    yul = float(row[2].replace(',', '.')) if len(row) > 2 else 0.0
                    fl = float(row[3].replace(',', '.')) if len(row) > 3 else 0.0
                    iku = float(row[4].replace(',', '.')) if len(row) > 4 else 0.0
                data.append((filial, score, yul, fl, iku))

            if data:
                return data
        except Exception:
            continue

    if not data:
        raise HTTPException(400, "Не удалось разобрать CSV. Ожидается формат: филиал, общий_балл, юл, фл, ику")
    return data


def parse_xml(content: bytes) -> list:
    """
    Парсит XML-файл.
    Ожидается структура:
        <ratings>
            <rating>
                <filial>Название</filial>
                <score>95.5</score>
                <yul>45.0</yul>
                <fl>30.0</fl>
                <iku>20.5</iku>
            </rating>
            ...
        </ratings>
    Или атрибуты:
        <rating filial="..." score="..." yul="..." fl="..." iku="..."/>
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise HTTPException(400, "Некорректный XML")

    data = []
    for rating_elem in root.findall('.//rating'):
        # Вариант с атрибутами
        filial = rating_elem.get('filial')
        score_str = rating_elem.get('score')
        yul_str = rating_elem.get('yul')
        fl_str = rating_elem.get('fl')
        iku_str = rating_elem.get('iku')

        if filial and score_str:
            try:
                score = float(score_str.replace(',', '.'))
                yul = float(yul_str.replace(',', '.')) if yul_str else 0.0
                fl = float(fl_str.replace(',', '.')) if fl_str else 0.0
                iku = float(iku_str.replace(',', '.')) if iku_str else 0.0
                data.append((filial.strip(), score, yul, fl, iku))
                continue
            except ValueError:
                pass

        # Вариант с дочерними элементами
        filial_elem = rating_elem.find('filial')
        score_elem = rating_elem.find('score')
        yul_elem = rating_elem.find('yul')
        fl_elem = rating_elem.find('fl')
        iku_elem = rating_elem.find('iku')

        if filial_elem is not None and score_elem is not None:
            filial = filial_elem.text
            score_str = score_elem.text
            if filial and score_str:
                try:
                    score = float(score_str.replace(',', '.'))
                    yul = float(yul_elem.text.replace(',', '.')) if yul_elem is not None and yul_elem.text else 0.0
                    fl = float(fl_elem.text.replace(',', '.')) if fl_elem is not None and fl_elem.text else 0.0
                    iku = float(iku_elem.text.replace(',', '.')) if iku_elem is not None and iku_elem.text else 0.0
                    data.append((filial.strip(), score, yul, fl, iku))
                except ValueError:
                    pass

    if not data:
        raise HTTPException(400, "Не найдены элементы rating с необходимыми полями (filial, score, yul, fl, iku)")
    return data


@router.post("/rating")
async def import_rating(
    file: UploadFile = File(...),
    period: str = Form(...),   # формат "2025-01-01"
    db: AsyncSession = Depends(get_db)
):
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

    # Сортируем по убыванию интегрального балла
    data.sort(key=lambda x: x[1], reverse=True)

    # Удаляем старый рейтинг за период
    await db.execute(delete(Rating).where(Rating.period == period_date))

    for rank, (filial_name, score, yul, fl, iku) in enumerate(data, start=1):
        # Находим или создаём филиал
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
            rank=rank,
            kpi1=yul,
            kpi2=fl,
            kpi3=iku
        )
        db.add(rating)

    await db.commit()
    return {"status": "ok", "imported": len(data), "period": period}