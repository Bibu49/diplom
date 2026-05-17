from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.db import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # имя загруженного файла
    filename = Column(String, nullable=False)

    # тип файла: xlsx / csv / xml
    file_type = Column(String, nullable=False)

    # статус импорта
    # uploaded / processing / completed / failed
    status = Column(String, default="uploaded")

    # сколько строк импортировано
    rows_count = Column(Integer, default=0)

    # дата импорта
    created_at = Column(DateTime, default=datetime.utcnow)

    # дата завершения обработки
    completed_at = Column(DateTime, nullable=True)

    # текст ошибки если импорт упал
    error_message = Column(String, nullable=True)