from fastapi import APIRouter, UploadFile, File
from tempfile import NamedTemporaryFile

from app.services.file_loader import FileLoader
from app.services.excel_parser import ExcelParser
from app.services.ul_calculator import ULCalculator
from app.services.rating_calculator import RatingCalculator

router = APIRouter(prefix='/api/import', tags=['import'])


@router.post('/excel')
async def import_excel(file: UploadFile = File(...)):

    with NamedTemporaryFile(delete=False) as temp:
        temp.write(await file.read())

        path = temp.name

    excel = FileLoader.load(path)

    parser = ExcelParser(excel)

    ul_df = parser.load_ul()

    ul_result = ULCalculator().calculate(
        ul_df,
        norm=0.95
    )

    return {
        'status': 'ok',
        'rows': len(ul_result)
    }