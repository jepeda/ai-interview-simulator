"""Earnings API. Run with `npm run dev` (port 8715). Swagger UI: http://127.0.0.1:8715/docs"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from earnings.db import DB_PATH, Base, SessionLocal, engine
from earnings.errors import register_error_handlers
from earnings.routers import earnings, providers, rates
from earnings.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Earnings API (AI interview)", lifespan=lifespan)
register_error_handlers(app)
app.include_router(providers.router)
app.include_router(earnings.router)
app.include_router(rates.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
