from fastapi import FastAPI
from app.routers import rating, filials, kpis, facts, import_rating, primary_import, auth
from contextlib import asynccontextmanager
from app.database.db import engine, Base
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title="KPI Service", description="Расчёт рейтингов филиалов")

app.include_router(rating.router)
app.include_router(filials.router)
app.include_router(kpis.router)
app.include_router(facts.router)
app.include_router(import_rating.router)
app.include_router(primary_import.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "KPI сервис работает"}

@app.get("/api/health")
def health():
    return {"status": "ok"}