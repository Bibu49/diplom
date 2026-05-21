from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.models.import_session import ImportSession

class Filial(Base):
    __tablename__ = "filials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    region = Column(String)

    kpi_facts = relationship("KpiFact", back_populates="filial")
    ratings = relationship("Rating", back_populates="filial")

class KPI(Base):
    __tablename__ = "kpis"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String)
    weight = Column(Float, default=1.0)   # вес в интегральном рейтинге
    target = Column(Float)                # плановое значение (может быть общим для всех)
    is_higher_better = Column(Integer, default=1)  # 1 - больше лучше, 0 - меньше лучше
    category = Column(String(20), nullable=True)

    kpi_facts = relationship("KpiFact", back_populates="kpi")

class KpiFact(Base):
    __tablename__ = "kpi_facts"
    id = Column(Integer, primary_key=True, index=True)
    filial_id = Column(Integer, ForeignKey("filials.id"))
    kpi_id = Column(Integer, ForeignKey("kpis.id"))
    period = Column(Date, nullable=False)
    value = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('filial_id', 'kpi_id', 'period', name='_filial_kpi_period_uc'),)

    filial = relationship("Filial", back_populates="kpi_facts")
    kpi = relationship("KPI", back_populates="kpi_facts")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    filial_id = Column(Integer, ForeignKey("filials.id"))
    period = Column(Date, nullable=False)
    score = Column(Float)      # интегральный балл
    rank = Column(Integer)     # место в рейтинге

    filial = relationship("Filial", back_populates="ratings")

class PrimaryData(Base):
    __tablename__ = "primary_data"
    id = Column(Integer, primary_key=True)
    filial_id = Column(Integer, ForeignKey("filials.id"), nullable=False)
    period = Column(Date, nullable=False)
    category = Column(String(10), nullable=False)  # 'ЮЛ', 'ФЛ', 'ИКУ'
    accrued = Column(Float, default=0.0)          # начислено
    advances = Column(Float, default=0.0)         # авансы
    realization = Column(Float, default=0.0)      # объём реализации
    debt_receivable = Column(Float, default=0.0)  # дебиторская задолженность (Дт)
    overdue_debt = Column(Float, default=0.0)     # просроченная задолженность (ПЗ)