from pydantic import BaseModel
from datetime import date
from typing import Optional

class FilialBase(BaseModel):
    name: str
    region: Optional[str] = None

class FilialCreate(FilialBase):
    pass

class Filial(FilialBase):
    id: int
    class Config:
        from_attributes = True

class KPICreate(BaseModel):
    name: str
    unit: Optional[str] = None
    weight: float = 1.0
    target: Optional[float] = None
    is_higher_better: bool = True

class KPI(KPICreate):
    id: int
    class Config:
        from_attributes = True

class KpiFactCreate(BaseModel):
    filial_id: int
    kpi_id: int
    period: date
    value: float

class RatingResponse(BaseModel):
    filial_id: int
    filial_name: str
    period: date
    score: float
    rank: int
    kpi1: Optional[float] = None
    kpi2: Optional[float] = None
    kpi3: Optional[float] = None